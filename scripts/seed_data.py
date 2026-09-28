#!/usr/bin/env python3
"""FR1.5 orchestrator — seeds the demo watershed + synthetic field records
through the REAL running API (never by writing to Postgres directly), so the
geo-integrity validator actually runs on every row and produces genuine
geo_flags/geo_score - the strongest evidence that ingestion works end to end.

Usage (with the API running, e.g. `uvicorn app.main:app` from /api):
    python scripts/seed_data.py [--base-url http://localhost:8000] [--regenerate]

Requires: requests, pyyaml (api/requirements-dev.txt has both).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed.config_loader import load_watershed_config
from scripts.seed.generate_placeholder_photos import PHOTOS_DIR, generate_photos
from scripts.seed.generate_records_csv import OUTPUT_CSV, generate_rows, write_csv


def _post_mws(base_url: str, config) -> None:
    import json

    with open(config.boundary_path, encoding="utf-8") as f:
        boundary = json.load(f)

    payload = {
        "id": config.id,
        "name": config.name,
        "project_id": config.project_id,
        "state": config.state,
        "district": config.district,
        "boundary": {"type": boundary["type"], "coordinates": boundary["coordinates"]},
        "baseline_start": config.baseline_start,
        "baseline_end": config.baseline_end,
        "latest_start": config.latest_start,
        "latest_end": config.latest_end,
        "is_synthetic_boundary": config.is_synthetic_boundary,
    }

    existing = requests.get(f"{base_url}/mws/{config.id}", timeout=10)
    if existing.status_code == 200:
        print(f"mws {config.id} already exists, skipping POST /mws")
        return

    resp = requests.post(f"{base_url}/mws", json=payload, timeout=10)
    if resp.status_code != 201:
        raise RuntimeError(f"POST /mws failed ({resp.status_code}): {resp.text}")
    print(f"Created mws {config.id} ({config.name})")


def _post_record(base_url: str, row: dict, photo_path: Path) -> dict:
    metadata = {
        "work_code": row["work_code"],
        "mws_id": row["mws_id"],
        "category": row["category"],
        "activity": row["activity"],
        "status": row["status"],
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "gps_accuracy_m": float(row["gps_accuracy_m"]),
        "orientation": float(row["orientation"]),
        "captured_at": row["captured_at"],
        "remarks": row["remarks"],
        "observer_id": row["observer_id"],
        "observer_name": row["observer_name"],
        "organisation": row["organisation"],
        "is_synthetic": row["is_synthetic"].lower() == "true",
        "photo_source": row["photo_source"],
    }
    import json

    with open(photo_path, "rb") as photo_file:
        resp = requests.post(
            f"{base_url}/records",
            data={"metadata": json.dumps(metadata)},
            files={"photo1": (photo_path.name, photo_file, "image/jpeg")},
            timeout=30,
        )
    if resp.status_code != 201:
        raise RuntimeError(f"POST /records failed for {row['row_id']} ({resp.status_code}): {resp.text}")
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--regenerate", action="store_true", help="regenerate CSV + photos before seeding")
    args = parser.parse_args()

    config = load_watershed_config()

    if args.regenerate or not OUTPUT_CSV.exists():
        rows = generate_rows()
        write_csv(rows)
        generate_photos()
    if not PHOTOS_DIR.exists() or not any(PHOTOS_DIR.iterdir()):
        generate_photos()

    _post_mws(args.base_url, config)

    with open(OUTPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"\nIngesting {len(rows)} records via POST {args.base_url}/records ...\n")
    n_ok, n_fail = 0, 0
    for row in rows:
        photo_path = PHOTOS_DIR / f"{row['row_id']}.jpg"
        try:
            result = _post_record(args.base_url, row, photo_path)
        except RuntimeError as exc:
            print(f"  [FAIL] {row['row_id']}: {exc}")
            n_fail += 1
            continue
        n_ok += 1
        geo = result["geo_integrity"]
        # "zero" = rule scored 0 points outright (a real failure); "partial" = scored
        # some but not full points (e.g. gps_accuracy in the 10-25m band) - distinct
        # from a failure, just not full marks. geo_score itself is the ground truth.
        zero = [f["rule"] for f in geo["geo_flags"] if f["points"] == 0]
        partial = [f["rule"] for f in geo["geo_flags"] if 0 < f["points"] < f["max"]]
        tag = " <- PLANTED BAD ROW" if row["bad_row_type"] else ""
        print(
            f"  [OK] {row['row_id']:28s} geo_score={geo['geo_score']:2d}/30  "
            f"zero={zero or 'none'} partial={partial or 'none'}{tag}"
        )

    print(f"\nDone: {n_ok} ingested, {n_fail} failed.")


if __name__ == "__main__":
    main()
