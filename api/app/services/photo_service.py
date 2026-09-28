"""Photo persistence, pHash, and EXIF extraction for POST /records.

Storage is local disk for Phase 1 (PHOTO_STORAGE_DIR) — no object-storage
service is in the locked stack yet. Swappable later without a schema change
since only photo1_url/photo2_url (plain TEXT) are stored.
"""

from __future__ import annotations

import datetime as dt
import io
import uuid
from pathlib import Path

import exifread
import imagehash
from PIL import Image

from app.config import get_settings
from app.services.geo_integrity import ExifData


def compute_phash(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as img:
        return str(imagehash.phash(img))


def _to_degrees(value) -> float:
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)


def _extract_gps(tags: dict) -> tuple[float, float] | None:
    lat_tag = tags.get("GPS GPSLatitude")
    lon_tag = tags.get("GPS GPSLongitude")
    if lat_tag is None or lon_tag is None:
        return None
    lat = _to_degrees(lat_tag)
    lat_ref = tags.get("GPS GPSLatitudeRef")
    if lat_ref is not None and str(lat_ref) == "S":
        lat = -lat
    lon = _to_degrees(lon_tag)
    lon_ref = tags.get("GPS GPSLongitudeRef")
    if lon_ref is not None and str(lon_ref) == "W":
        lon = -lon
    return (lat, lon)


def _extract_datetime(tags: dict) -> dt.datetime | None:
    for key in ("EXIF DateTimeOriginal", "Image DateTime"):
        raw = tags.get(key)
        if raw is None:
            continue
        try:
            return dt.datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            continue
    return None


def extract_exif(image_bytes: bytes) -> ExifData:
    tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
    return ExifData(gps=_extract_gps(tags), captured_at=_extract_datetime(tags))


def save_photo(image_bytes: bytes, suffix: str = ".jpg") -> tuple[str, str]:
    """Persist an uploaded photo to disk. Returns (filename, public_url)."""
    settings = get_settings()
    storage_dir = Path(settings.photo_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (storage_dir / filename).write_bytes(image_bytes)
    public_url = f"{settings.photo_public_base_url.rstrip('/')}/{filename}"
    return filename, public_url
