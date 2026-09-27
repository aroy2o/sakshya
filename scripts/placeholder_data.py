"""
Placeholder MWS boundary + asset point generator.

Used ONLY when the real HydroBASINS polygon (needs GEE credentials, which
this session doesn't have) and backend-engineer's real seed data (Round 1
hadn't landed as of this run) are both unavailable — per this agent's role
brief: "you can start immediately... generate your own placeholder
boundary + asset points (Shapely random-point-in-polygon) if needed."

Every output sets is_synthetic_boundary / is_synthetic = true, per
CLAUDE.md's "is_synthetic is never optional" rule — this is a clearly
labeled stand-in, never presented as the official Marigaon MWS polygon.

Reference point used only to keep the demo geographically plausible: the
approximate centre of Morigaon district, Assam (~26.28N, 92.35E). The
polygon itself is a generated placeholder shape, NOT the actual
HydroBASINS L12 boundary for HYBAS_ID 4120883730.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from shapely.geometry import Point, Polygon, mapping

import config

MORIGAON_CENTER_LON = 92.3450
MORIGAON_CENTER_LAT = 26.2800
_HALF_EXTENT_DEG = 0.035  # roughly a few km across at this latitude — micro-watershed scale

CATEGORIES = ["AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"]  # PRD §15.1, fixed set
ACTIVITIES = {
    "AM": "Contour Bund",
    "VM": "Block Plantation",
    "SM": "Check Dam",
    "PT": "Farm Pond",
    "NC": "Nala Deepening",
    "BN": "Field Bund",
    "LS": "Cattle Shelter",
    "LH": "Horticulture",
    "OM": "Jungle Clearance",
}


def generate_placeholder_boundary() -> dict:
    """An irregular octagon around the Morigaon reference point (deliberately
    not a perfect square, so it doesn't read as an obviously synthetic box
    on the map)."""
    cx, cy = MORIGAON_CENTER_LON, MORIGAON_CENTER_LAT
    offsets = [
        (1.0, 0.3), (0.7, 0.9), (0.1, 1.0), (-0.6, 0.8),
        (-1.0, 0.2), (-0.8, -0.7), (-0.1, -1.0), (0.9, -0.6),
    ]
    coords = [(cx + dx * _HALF_EXTENT_DEG, cy + dy * _HALF_EXTENT_DEG) for dx, dy in offsets]
    coords.append(coords[0])
    poly = Polygon(coords)
    return {
        "mws_id": config.MWS_ID,
        "name": config.MWS_NAME,
        "is_synthetic_boundary": True,
        "note": (
            "Generated placeholder polygon, not the official HydroBASINS L12 "
            "boundary — GEE credentials were unavailable this session. Swap "
            "for the real boundary at zero code cost once fetchable via "
            "gee_client.fetch_hydrobasin_boundary()."
        ),
        "geometry": mapping(poly),
    }


def generate_placeholder_assets(n: int = 20, seed: int = 42) -> list[dict]:
    """Shapely random-point-in-polygon asset generation — same approach PRD
    FR1.5 specifies for the backend seed script, so the shape is compatible
    with whatever backend-engineer lands."""
    rng = random.Random(seed)
    boundary = generate_placeholder_boundary()
    poly = Polygon(boundary["geometry"]["coordinates"][0])
    minx, miny, maxx, maxy = poly.bounds

    assets: list[dict] = []
    attempts = 0
    max_attempts = n * 200
    while len(assets) < n and attempts < max_attempts:
        attempts += 1
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        if not poly.contains(Point(x, y)):
            continue
        category = CATEGORIES[len(assets) % len(CATEGORIES)]
        assets.append(
            {
                "record_id": len(assets) + 1,
                "mws_id": config.MWS_ID,
                "category": category,
                "activity": ACTIVITIES[category],
                "lat": round(y, 6),
                "lon": round(x, 6),
                "is_synthetic": True,
                "photo_source": "unknown",  # geospatial placeholder points carry no photo at all
            }
        )

    if len(assets) < n:
        raise RuntimeError(
            f"Placeholder point generation only found {len(assets)}/{n} points "
            f"inside the polygon after {attempts} attempts — check polygon bounds."
        )
    return assets


def write_placeholder_inputs() -> tuple[Path, Path]:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    boundary = generate_placeholder_boundary()
    boundary_path = config.OUTPUT_DIR / "placeholder_boundary.geojson"
    boundary_path.write_text(json.dumps(boundary, indent=2))

    assets = generate_placeholder_assets()
    assets_path = config.OUTPUT_DIR / "placeholder_assets.json"
    assets_path.write_text(json.dumps(assets, indent=2))

    return boundary_path, assets_path


if __name__ == "__main__":
    b, a = write_placeholder_inputs()
    print(f"Wrote placeholder boundary: {b}")
    print(f"Wrote placeholder assets: {a}")
