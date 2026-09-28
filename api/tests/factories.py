"""Test-only helpers for building in-memory JPEGs with (or without) injected
EXIF GPS/timestamp tags - shared by the integration tests. Mirrors what the
seed script's photo generator does for real seed data (scripts/seed/).
"""

from __future__ import annotations

import datetime as dt
import io

import piexif
from PIL import Image


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


def make_jpeg_bytes(
    lat: float | None = None,
    lon: float | None = None,
    captured_at: dt.datetime | None = None,
    include_exif: bool = True,
    color: tuple[int, int, int] = (120, 180, 90),
) -> bytes:
    """Build a tiny in-memory JPEG, optionally with EXIF GPS + DateTimeOriginal."""
    img = Image.new("RGB", (64, 64), color=color)
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

    img.save(buf, format="jpeg", exif=exif_bytes)
    return buf.getvalue()
