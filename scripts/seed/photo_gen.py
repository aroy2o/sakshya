"""Placeholder JPEG generation with injected EXIF (FR1.5).

No real photography or external image-generation API for Phase 1 (that's
Phase 2's FR2.0 scope, e.g. Pollinations.ai) - Pillow draws a simple labeled
placeholder image, and piexif injects GPS/timestamp EXIF tags that match (or,
for the missing-EXIF bad row, are simply omitted).
"""

from __future__ import annotations

import io
import random
from datetime import datetime

import piexif
from PIL import Image, ImageDraw

# Deterministic color per category so photos are visually distinguishable in
# a demo without needing real imagery.
CATEGORY_COLORS: dict[str, tuple[int, int, int]] = {
    "AM": (150, 140, 60),
    "VM": (60, 140, 60),
    "SM": (120, 120, 130),
    "PT": (50, 110, 170),
    "NC": (70, 130, 180),
    "BN": (150, 100, 60),
    "LS": (170, 120, 90),
    "LH": (140, 90, 150),
    "OM": (110, 110, 110),
}
DEFAULT_COLOR = (100, 100, 100)
IMAGE_SIZE = (320, 240)
GRID_COLS, GRID_ROWS = 10, 8  # mosaic tiles - gives distinct rows enough low-frequency
                                # variation that pHash doesn't false-flag them as duplicates
                                # (a flat color block + a few lines of text hashes almost
                                # identically across rows, which is what real duplicate
                                # detection is supposed to catch - so distinct rows need a
                                # genuinely different image, not just different text on it)
JITTER = 70


def _deg_to_dms_rational(value: float) -> list[tuple[int, int]]:
    deg = int(value)
    minutes_full = (value - deg) * 60
    minute = int(minutes_full)
    second = round((minutes_full - minute) * 60 * 100)
    return [(deg, 1), (minute, 1), (second, 100)]


def _gps_ifd(lat: float, lon: float) -> dict:
    return {
        piexif.GPSIFD.GPSLatitudeRef: "N" if lat >= 0 else "S",
        piexif.GPSIFD.GPSLatitude: _deg_to_dms_rational(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: "E" if lon >= 0 else "W",
        piexif.GPSIFD.GPSLongitude: _deg_to_dms_rational(abs(lon)),
    }


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def _draw_mosaic(img: Image.Image, base_color: tuple[int, int, int], seed_key: str) -> None:
    """Fills the image with a seeded random mosaic of tiles jittered around
    base_color. Two calls with the same seed_key produce visually (and, since
    we don't antialias, near-pixel-identical) matching output; two different
    seed_keys produce images far enough apart in pHash space that they never
    collide with DUPLICATE_HAMMING_THRESHOLD in services/geo_integrity.py -
    unlike a flat color block with a few words of text on it, which pHash
    (correctly) treats as near-identical regardless of the text."""
    rng = random.Random(seed_key)
    cell_w = IMAGE_SIZE[0] // GRID_COLS
    cell_h = IMAGE_SIZE[1] // GRID_ROWS
    draw = ImageDraw.Draw(img)
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            jitter = lambda c: _clamp(c + rng.randint(-JITTER, JITTER))  # noqa: E731
            cell_color = tuple(jitter(c) for c in base_color)
            x0, y0 = col * cell_w, row * cell_h
            draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=cell_color)


def build_photo(
    category: str,
    label: str,
    lat: float | None,
    lon: float | None,
    captured_at: datetime | None,
    include_exif: bool,
    seed_key: str | None = None,
) -> bytes:
    color = CATEGORY_COLORS.get(category, DEFAULT_COLOR)
    img = Image.new("RGB", IMAGE_SIZE, color=color)
    _draw_mosaic(img, color, seed_key or label)
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, IMAGE_SIZE[0] - 8, IMAGE_SIZE[1] - 8], outline=(255, 255, 255), width=2)
    draw.text((16, 16), "SAKSHYA — SYNTHETIC DEMO PHOTO", fill=(255, 255, 255))
    draw.text((16, 40), f"category: {category}", fill=(255, 255, 255))
    draw.text((16, 60), label, fill=(255, 255, 255))
    if lat is not None and lon is not None:
        draw.text((16, 80), f"lat/lon: {lat:.5f}, {lon:.5f}", fill=(255, 255, 255))
    if captured_at is not None:
        draw.text((16, 100), f"captured: {captured_at.isoformat()}", fill=(255, 255, 255))
    draw.text((16, IMAGE_SIZE[1] - 32), "AI-GENERATED PLACEHOLDER - NOT A REAL FIELD PHOTO", fill=(255, 220, 0))

    buf = io.BytesIO()
    exif_bytes = b""
    if include_exif and (lat is not None or captured_at is not None):
        exif_dict: dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        if captured_at is not None:
            ts = captured_at.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = ts
            exif_dict["0th"][piexif.ImageIFD.DateTime] = ts
        if lat is not None and lon is not None:
            exif_dict["GPS"] = _gps_ifd(lat, lon)
        exif_bytes = piexif.dump(exif_dict)

    img.save(buf, format="jpeg", exif=exif_bytes, quality=85)
    return buf.getvalue()
