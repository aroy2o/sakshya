"""FR1.5 — generate a CSV of synthetic DRISHTI-schema field records.

Coordinates are placed programmatically inside the actual watershed boundary
polygon via Shapely (reject-sampling random points), never hand-typed, so
this stays valid regardless of which watershed scripts/config/watershed.yaml
points at.

Includes 4 deliberately-bad rows (PRD §10 FR1.5 asks for "3-4"):
  1. duplicate_photo  - shares its photo_ref with another row (identical image)
  2. out_of_boundary  - point generated outside the polygon
  3. bad_gps_accuracy - gps_accuracy_m > 25
  4. missing_exif     - photo generated with no EXIF tags at all

("future timestamp" is the 5th failure mode FR1.6 asks pytest to cover; PRD
only asks for 3-4 *seeded* bad rows, and FR1.6 lists future-timestamp under
pytest coverage specifically, not under FR1.5's seed-row list — so it's
covered by tests/test_geo_integrity.py instead of a seeded DB row.)

Every row: is_synthetic=true, photo_source='ai_generated' (FR1.5 - no field
visit in this timeline).
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path

from shapely.geometry import Point, shape

from scripts.seed.config_loader import REPO_ROOT, load_watershed_config

OUTPUT_DIR = REPO_ROOT / "scripts" / "seed" / "output"
OUTPUT_CSV = OUTPUT_DIR / "field_records_seed.csv"

N_GOOD_ROWS = 12
RANDOM_SEED = 42  # reproducible demo data

CATEGORY_ACTIVITIES: dict[str, list[str]] = {
    "AM": ["Bench Terracing", "Contour Bund (Agronomic)", "Agro-forestry"],
    "VM": ["Block Plantation", "Grass Turfing", "Farm Forestry"],
    "SM": ["Check Dam", "Boulder Structure", "Cattle-proof Trench"],
    "PT": ["Farm Pond", "Percolation Tank", "Recharge Pit"],
    "NC": ["Nala Deepening", "Diversion Channel", "Gully Check"],
    "BN": ["Contour Bund", "Field Bund", "Earthen Bund"],
    "LS": ["Animal Health Camp", "Shelter for Cattle"],
    "LH": ["Horticulture", "Sericulture"],
    "OM": ["Jungle Clearance", "Agro Service Centre"],
}
STATUSES = ["completed", "ongoing", "completed", "completed"]  # weighted toward completed for the demo
OBSERVER_NAMES = ["A. Sharma", "R. Kalita", "P. Das", "M. Bora", "S. Gogoi"]
ORGANISATIONS = ["WCDC Morigaon", "SLNA Assam (demo)"]


@dataclass
class SeedRow:
    row_id: str
    work_code: str
    mws_id: str
    category: str
    activity: str
    status: str
    lat: float
    lon: float
    gps_accuracy_m: float
    orientation: float
    captured_at: str
    remarks: str
    observer_id: str
    observer_name: str
    organisation: str
    is_synthetic: bool
    photo_source: str
    bad_row_type: str  # "" for good rows
    photo_ref: str  # rows sharing a photo_ref get byte-identical generated images
    include_exif: bool


def _random_point_in_polygon(polygon, rng: random.Random) -> tuple[float, float]:
    minx, miny, maxx, maxy = polygon.bounds
    for _ in range(1000):
        candidate = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if polygon.contains(candidate):
            return candidate.y, candidate.x  # (lat, lon)
    raise RuntimeError("could not sample a point inside the boundary polygon after 1000 tries")


def _random_point_outside_polygon(polygon, rng: random.Random) -> tuple[float, float]:
    minx, miny, maxx, maxy = polygon.bounds
    width, height = maxx - minx, maxy - miny
    for _ in range(1000):
        # sample from a ring well outside the bounding box
        candidate = Point(rng.uniform(minx - width, maxx + width), rng.uniform(miny - height, maxy + height))
        if not polygon.contains(candidate):
            return candidate.y, candidate.x
    raise RuntimeError("could not sample a point outside the boundary polygon after 1000 tries")


def _random_captured_at(window_start: date, window_end: date, rng: random.Random) -> datetime:
    span_days = (window_end - window_start).days
    offset = rng.randint(0, max(span_days, 0))
    day = window_start + timedelta(days=offset)
    hour = rng.randint(7, 17)  # plausible daylight field-visit hour
    minute = rng.randint(0, 59)
    return datetime(day.year, day.month, day.day, hour, minute, 0)


def generate_rows(config_path: str | None = None, seed: int = RANDOM_SEED) -> list[SeedRow]:
    config = load_watershed_config(config_path)
    with open(config.boundary_path, encoding="utf-8") as f:
        import json

        boundary_geojson = json.load(f)
    polygon = shape(boundary_geojson)

    rng = random.Random(seed)
    window_start = date.fromisoformat(config.baseline_start)
    window_end = date.fromisoformat(config.latest_end)

    rows: list[SeedRow] = []
    codes = list(CATEGORY_ACTIVITIES.keys())

    # --- good rows ---
    for i in range(N_GOOD_ROWS):
        category = codes[i % len(codes)]
        activity = rng.choice(CATEGORY_ACTIVITIES[category])
        lat, lon = _random_point_in_polygon(polygon, rng)
        captured_at = _random_captured_at(window_start, window_end, rng)
        rows.append(
            SeedRow(
                row_id=f"good_{i:02d}",
                work_code=f"WC-{category}-{i:04d}",
                mws_id=config.id,
                category=category,
                activity=activity,
                status=rng.choice(STATUSES),
                lat=lat,
                lon=lon,
                gps_accuracy_m=round(rng.uniform(3.0, 15.0), 1),
                orientation=round(rng.uniform(0, 359), 1),
                captured_at=captured_at.isoformat(),
                remarks="Seeded demo record - synthetic, see photo_source.",
                observer_id=f"OBS{i % len(OBSERVER_NAMES) + 1}",
                observer_name=OBSERVER_NAMES[i % len(OBSERVER_NAMES)],
                organisation=ORGANISATIONS[i % len(ORGANISATIONS)],
                is_synthetic=True,
                photo_source="ai_generated",
                bad_row_type="",
                photo_ref=f"photo_good_{i:02d}",
                include_exif=True,
            )
        )

    # --- bad row 1: duplicate photo (two records, same photo_ref) ---
    for j, suffix in enumerate(["a", "b"]):
        lat, lon = _random_point_in_polygon(polygon, rng)
        captured_at = _random_captured_at(window_start, window_end, rng)
        rows.append(
            SeedRow(
                row_id=f"bad_duplicate_photo_{suffix}",
                work_code=f"WC-DUP-{j:02d}",
                mws_id=config.id,
                category="PT",
                activity="Farm Pond",
                status="completed",
                lat=lat,
                lon=lon,
                gps_accuracy_m=round(rng.uniform(3.0, 15.0), 1),
                orientation=0.0,
                captured_at=captured_at.isoformat(),
                remarks="PLANTED BAD ROW: duplicate photo reused across two records.",
                observer_id="OBS_BAD",
                observer_name="Bad Row Generator",
                organisation=ORGANISATIONS[0],
                is_synthetic=True,
                photo_source="ai_generated",
                bad_row_type="duplicate_photo",
                photo_ref="photo_duplicate_shared",  # SAME ref for both rows - byte-identical image
                include_exif=True,
            )
        )

    # --- bad row 2: out-of-boundary point ---
    lat, lon = _random_point_outside_polygon(polygon, rng)
    captured_at = _random_captured_at(window_start, window_end, rng)
    rows.append(
        SeedRow(
            row_id="bad_out_of_boundary",
            work_code="WC-OOB-00",
            mws_id=config.id,
            category="SM",
            activity="Check Dam",
            status="completed",
            lat=lat,
            lon=lon,
            gps_accuracy_m=round(rng.uniform(3.0, 15.0), 1),
            orientation=0.0,
            captured_at=captured_at.isoformat(),
            remarks="PLANTED BAD ROW: point placed just outside the mws boundary.",
            observer_id="OBS_BAD",
            observer_name="Bad Row Generator",
            organisation=ORGANISATIONS[0],
            is_synthetic=True,
            photo_source="ai_generated",
            bad_row_type="out_of_boundary",
            photo_ref="photo_out_of_boundary",
            include_exif=True,
        )
    )

    # --- bad row 3: gps_accuracy_m > 25 ---
    lat, lon = _random_point_in_polygon(polygon, rng)
    captured_at = _random_captured_at(window_start, window_end, rng)
    rows.append(
        SeedRow(
            row_id="bad_gps_accuracy",
            work_code="WC-GPS-00",
            mws_id=config.id,
            category="BN",
            activity="Contour Bund",
            status="completed",
            lat=lat,
            lon=lon,
            gps_accuracy_m=40.0,
            orientation=0.0,
            captured_at=captured_at.isoformat(),
            remarks="PLANTED BAD ROW: gps_accuracy_m exceeds the 25m threshold.",
            observer_id="OBS_BAD",
            observer_name="Bad Row Generator",
            organisation=ORGANISATIONS[0],
            is_synthetic=True,
            photo_source="ai_generated",
            bad_row_type="bad_gps_accuracy",
            photo_ref="photo_bad_gps_accuracy",
            include_exif=True,
        )
    )

    # --- bad row 4: missing EXIF entirely ---
    lat, lon = _random_point_in_polygon(polygon, rng)
    captured_at = _random_captured_at(window_start, window_end, rng)
    rows.append(
        SeedRow(
            row_id="bad_missing_exif",
            work_code="WC-EXIF-00",
            mws_id=config.id,
            category="VM",
            activity="Block Plantation",
            status="completed",
            lat=lat,
            lon=lon,
            gps_accuracy_m=round(rng.uniform(3.0, 15.0), 1),
            orientation=0.0,
            captured_at=captured_at.isoformat(),
            remarks="PLANTED BAD ROW: photo carries no EXIF GPS/timestamp at all.",
            observer_id="OBS_BAD",
            observer_name="Bad Row Generator",
            organisation=ORGANISATIONS[0],
            is_synthetic=True,
            photo_source="ai_generated",
            bad_row_type="missing_exif",
            photo_ref="photo_missing_exif",
            include_exif=False,
        )
    )

    return rows


def write_csv(rows: list[SeedRow], output_path: Path = OUTPUT_CSV) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    return output_path


def main() -> None:
    rows = generate_rows()
    path = write_csv(rows)
    n_bad = sum(1 for r in rows if r.bad_row_type)
    print(f"Wrote {len(rows)} rows ({len(rows) - n_bad} good, {n_bad} deliberately bad) to {path}")


if __name__ == "__main__":
    main()
