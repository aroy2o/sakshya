"""Geo-integrity validator — PRD.md §12.1 (FR1.4).

Pure, DB-independent module: every input the validator needs (mws boundary as
a shapely geometry, the submitted record's fields, EXIF already extracted
from the photo(s), and every other stored photo's pHash) is handed in by the
caller (app/routers/records.py does the DB/file I/O). This keeps the whole
rule set unit-testable with zero DB or network access — see
tests/test_geo_integrity.py.

Rule slugs below are canonical across the whole team (backend + frontend) —
do not rename without flagging it, frontend-engineer's UI checklist keys off
these exact strings.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import imagehash
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from app.services.geo_utils import haversine_m

# --- canonical rule slugs ---------------------------------------------------
RULE_GPS_ACCURACY = "gps_accuracy"
RULE_INSIDE_BOUNDARY = "inside_boundary"
RULE_EXIF_CONSISTENCY = "exif_consistency"
RULE_DUPLICATE_PHOTO = "duplicate_photo"
RULE_TIMESTAMP_SANE = "timestamp_sane"

# --- tunables named per CLAUDE.md's "named constants, not magic numbers" ---
GPS_ACCURACY_GOOD_M = 10.0
GPS_ACCURACY_OK_M = 25.0
EXIF_GPS_TOLERANCE_M = 100.0
DUPLICATE_HAMMING_THRESHOLD = 6  # distance > 6 passes; <= 6 counts as a duplicate

POINTS_GPS_ACCURACY_MAX = 8
POINTS_INSIDE_BOUNDARY_MAX = 8
POINTS_EXIF_CONSISTENCY_MAX = 6
POINTS_DUPLICATE_PHOTO_MAX = 5
POINTS_TIMESTAMP_SANE_MAX = 3
GEO_SCORE_MAX = (
    POINTS_GPS_ACCURACY_MAX
    + POINTS_INSIDE_BOUNDARY_MAX
    + POINTS_EXIF_CONSISTENCY_MAX
    + POINTS_DUPLICATE_PHOTO_MAX
    + POINTS_TIMESTAMP_SANE_MAX
)  # 30, per PRD §12.1


@dataclass
class ExifData:
    """EXIF fields extracted from a photo, already parsed to plain Python types."""

    gps: tuple[float, float] | None = None  # (lat, lon)
    captured_at: dt.datetime | None = None


@dataclass
class GeoFlag:
    rule: str
    passed: bool
    points: int
    max: int  # noqa: A003 - intentional: matches the {rule, passed, points, max, detail} API contract
    detail: str


@dataclass
class GeoIntegrityResult:
    geo_score: int
    geo_flags: list[GeoFlag]


@dataclass
class GeoIntegrityInput:
    lat: float
    lon: float
    gps_accuracy_m: float | None
    captured_at: dt.datetime | None
    boundary: BaseGeometry  # mws geometry, WGS84 (lon, lat) ordering as shapely expects
    window_start: dt.date | None
    window_end: dt.date | None
    now: dt.datetime
    photo1_exif: ExifData | None
    photo1_phash: str | None
    photo2_phash: str | None
    existing_phashes: list[str]  # every other stored record's photo1_phash/photo2_phash


def _ensure_aware_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value


def _score_gps_accuracy(acc: float | None) -> GeoFlag:
    if acc is None:
        return GeoFlag(RULE_GPS_ACCURACY, False, 0, POINTS_GPS_ACCURACY_MAX, "gps_accuracy_m missing")
    if acc <= GPS_ACCURACY_GOOD_M:
        return GeoFlag(
            RULE_GPS_ACCURACY, True, 8, POINTS_GPS_ACCURACY_MAX, f"{acc}m <= {GPS_ACCURACY_GOOD_M}m"
        )
    if acc <= GPS_ACCURACY_OK_M:
        return GeoFlag(
            RULE_GPS_ACCURACY,
            False,
            4,
            POINTS_GPS_ACCURACY_MAX,
            f"{acc}m within {GPS_ACCURACY_GOOD_M}-{GPS_ACCURACY_OK_M}m band (partial credit)",
        )
    return GeoFlag(
        RULE_GPS_ACCURACY, False, 0, POINTS_GPS_ACCURACY_MAX, f"{acc}m exceeds {GPS_ACCURACY_OK_M}m threshold"
    )


def _score_inside_boundary(lat: float, lon: float, boundary: BaseGeometry) -> GeoFlag:
    point = Point(lon, lat)
    # Shapely .contains() is GEOS-backed, same engine/semantics as PostGIS's
    # ST_Contains (which PRD §12.1 names) - kept in-process so this validator
    # stays DB-free and unit-testable. Boundary-touching points are NOT
    # contained under this definition, matching ST_Contains' own semantics.
    inside = bool(boundary.contains(point))
    detail = "point falls inside mws boundary" if inside else "point falls outside mws boundary"
    return GeoFlag(RULE_INSIDE_BOUNDARY, inside, 8 if inside else 0, POINTS_INSIDE_BOUNDARY_MAX, detail)


def _score_exif_consistency(
    submitted_lat: float,
    submitted_lon: float,
    submitted_captured_at: dt.datetime | None,
    exif: ExifData | None,
) -> GeoFlag:
    has_gps = exif is not None and exif.gps is not None
    has_time = exif is not None and exif.captured_at is not None

    if not has_gps and not has_time:
        return GeoFlag(
            RULE_EXIF_CONSISTENCY,
            False,
            0,
            POINTS_EXIF_CONSISTENCY_MAX,
            "no EXIF GPS or timestamp found on photo",
        )

    gps_match = False
    if has_gps:
        assert exif is not None and exif.gps is not None
        dist = haversine_m(submitted_lat, submitted_lon, exif.gps[0], exif.gps[1])
        gps_match = dist <= EXIF_GPS_TOLERANCE_M

    time_match = False
    if has_time and submitted_captured_at is not None:
        assert exif is not None and exif.captured_at is not None
        time_match = exif.captured_at.date() == submitted_captured_at.date()

    if has_gps and has_time:
        if gps_match and time_match:
            return GeoFlag(
                RULE_EXIF_CONSISTENCY,
                True,
                6,
                POINTS_EXIF_CONSISTENCY_MAX,
                "EXIF GPS and timestamp both present and consistent with submitted metadata",
            )
        if gps_match or time_match:
            return GeoFlag(
                RULE_EXIF_CONSISTENCY,
                False,
                3,
                POINTS_EXIF_CONSISTENCY_MAX,
                "EXIF GPS and timestamp both present but only one matches submitted metadata",
            )
        return GeoFlag(
            RULE_EXIF_CONSISTENCY,
            False,
            0,
            POINTS_EXIF_CONSISTENCY_MAX,
            "EXIF GPS and timestamp both present but neither matches submitted metadata",
        )

    # exactly one of GPS/timestamp present in EXIF at all
    return GeoFlag(
        RULE_EXIF_CONSISTENCY,
        False,
        3,
        POINTS_EXIF_CONSISTENCY_MAX,
        "only one of EXIF GPS/timestamp present on photo (partial credit)",
    )


def _score_duplicate_photo(
    photo1_phash: str | None, photo2_phash: str | None, existing_phashes: list[str]
) -> GeoFlag:
    candidates = [p for p in (photo1_phash, photo2_phash) if p]
    if not candidates:
        return GeoFlag(
            RULE_DUPLICATE_PHOTO, True, 5, POINTS_DUPLICATE_PHOTO_MAX, "no photo hash available to compare"
        )

    min_distance: int | None = None
    for cand in candidates:
        try:
            cand_hash = imagehash.hex_to_hash(cand)
        except ValueError:
            continue
        for existing in existing_phashes:
            try:
                existing_hash = imagehash.hex_to_hash(existing)
            except ValueError:
                continue
            distance = int(cand_hash - existing_hash)
            if min_distance is None or distance < min_distance:
                min_distance = distance

    if min_distance is not None and min_distance <= DUPLICATE_HAMMING_THRESHOLD:
        return GeoFlag(
            RULE_DUPLICATE_PHOTO,
            False,
            0,
            POINTS_DUPLICATE_PHOTO_MAX,
            f"near-duplicate photo found (hamming distance {min_distance} <= {DUPLICATE_HAMMING_THRESHOLD})",
        )
    return GeoFlag(
        RULE_DUPLICATE_PHOTO,
        True,
        5,
        POINTS_DUPLICATE_PHOTO_MAX,
        "no near-duplicate photo found among stored records",
    )


def _score_timestamp_sane(
    captured_at: dt.datetime | None,
    window_start: dt.date | None,
    window_end: dt.date | None,
    now: dt.datetime,
) -> GeoFlag:
    if captured_at is None:
        return GeoFlag(RULE_TIMESTAMP_SANE, False, 0, POINTS_TIMESTAMP_SANE_MAX, "captured_at missing")

    captured_at_aware = _ensure_aware_utc(captured_at)
    now_aware = _ensure_aware_utc(now)

    if captured_at_aware > now_aware:
        return GeoFlag(
            RULE_TIMESTAMP_SANE, False, 0, POINTS_TIMESTAMP_SANE_MAX, "captured_at is in the future"
        )

    cap_date = captured_at_aware.date()
    if window_start is not None and cap_date < window_start:
        return GeoFlag(
            RULE_TIMESTAMP_SANE,
            False,
            0,
            POINTS_TIMESTAMP_SANE_MAX,
            f"captured_at {cap_date} is before project window start {window_start}",
        )
    if window_end is not None and cap_date > window_end:
        return GeoFlag(
            RULE_TIMESTAMP_SANE,
            False,
            0,
            POINTS_TIMESTAMP_SANE_MAX,
            f"captured_at {cap_date} is after project window end {window_end}",
        )
    return GeoFlag(
        RULE_TIMESTAMP_SANE,
        True,
        3,
        POINTS_TIMESTAMP_SANE_MAX,
        "captured_at within project window and not future-dated",
    )


def evaluate(inp: GeoIntegrityInput) -> GeoIntegrityResult:
    flags = [
        _score_gps_accuracy(inp.gps_accuracy_m),
        _score_inside_boundary(inp.lat, inp.lon, inp.boundary),
        _score_exif_consistency(inp.lat, inp.lon, inp.captured_at, inp.photo1_exif),
        _score_duplicate_photo(inp.photo1_phash, inp.photo2_phash, inp.existing_phashes),
        _score_timestamp_sane(inp.captured_at, inp.window_start, inp.window_end, inp.now),
    ]
    geo_score = sum(f.points for f in flags)
    return GeoIntegrityResult(geo_score=geo_score, geo_flags=flags)
