"""FR1.5 — generate placeholder JPEGs (+ injected EXIF) for every row in
field_records_seed.csv. Rows sharing a `photo_ref` (the planted
duplicate-photo bad row) get byte-identical images, so the geo-integrity
validator's pHash check genuinely fires on ingest.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from scripts.seed.config_loader import REPO_ROOT
from scripts.seed.generate_records_csv import OUTPUT_CSV
from scripts.seed.photo_gen import build_photo

PHOTOS_DIR = REPO_ROOT / "scripts" / "seed" / "output" / "photos"


def generate_photos(csv_path: Path = OUTPUT_CSV, photos_dir: Path = PHOTOS_DIR) -> list[Path]:
    photos_dir.mkdir(parents=True, exist_ok=True)
    photo_ref_bytes: dict[str, bytes] = {}
    written: list[Path] = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            photo_ref = row["photo_ref"]
            if photo_ref not in photo_ref_bytes:
                captured_at = datetime.fromisoformat(row["captured_at"]) if row["captured_at"] else None
                include_exif = row["include_exif"].lower() == "true"
                photo_ref_bytes[photo_ref] = build_photo(
                    category=row["category"],
                    label=f"{row['work_code']} - {row['activity']}",
                    seed_key=photo_ref,
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    captured_at=captured_at,
                    include_exif=include_exif,
                )
            out_path = photos_dir / f"{row['row_id']}.jpg"
            out_path.write_bytes(photo_ref_bytes[photo_ref])
            written.append(out_path)

    return written


def main() -> None:
    written = generate_photos()
    n_unique = len({p.read_bytes() for p in written})
    print(f"Wrote {len(written)} photo files ({n_unique} distinct images) to {PHOTOS_DIR}")


if __name__ == "__main__":
    main()
