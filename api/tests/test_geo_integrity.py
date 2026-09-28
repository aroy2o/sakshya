"""FR1.6 - pytest coverage for services/geo_integrity.py.

No DB, no network: every fixture here is a plain Python/shapely value. This
file must never import the `client` fixture from conftest.py.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest
from imagehash import ImageHash
from shapely.geometry import Polygon

from app.services.geo_integrity import (
    RULE_DUPLICATE_PHOTO,
    RULE_EXIF_CONSISTENCY,
    RULE_GPS_ACCURACY,
    RULE_INSIDE_BOUNDARY,
    RULE_TIMESTAMP_SANE,
    ExifData,
    GeoIntegrityInput,
    evaluate,
)

BOUNDARY = Polygon([(91.95, 25.95), (92.05, 25.95), (92.05, 26.05), (91.95, 26.05), (91.95, 25.95)])
INSIDE_LAT, INSIDE_LON = 26.00, 92.00
OUTSIDE_LAT, OUTSIDE_LON = 27.00, 93.00
NOW = dt.datetime(2025, 6, 15, tzinfo=dt.UTC)
WINDOW_START = dt.date(2023, 1, 1)
WINDOW_END = dt.date(2025, 3, 31)
GOOD_CAPTURED_AT = dt.datetime(2025, 2, 1, 9, 0, 0, tzinfo=dt.UTC)


def _hash_with_n_bits_set(n: int) -> ImageHash:
    arr = np.zeros((8, 8), dtype=bool)
    flat = arr.reshape(-1)
    flat[:n] = True
    return ImageHash(arr)


def _flag(result, rule: str):
    return next(f for f in result.geo_flags if f.rule == rule)


def _base_input(**overrides) -> GeoIntegrityInput:
    defaults = dict(
        lat=INSIDE_LAT,
        lon=INSIDE_LON,
        gps_accuracy_m=5.0,
        captured_at=GOOD_CAPTURED_AT,
        boundary=BOUNDARY,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        now=NOW,
        photo1_exif=ExifData(gps=(INSIDE_LAT, INSIDE_LON), captured_at=dt.datetime(2025, 2, 1, 9, 0, 0)),
        photo1_phash=str(_hash_with_n_bits_set(0)),
        photo2_phash=None,
        existing_phashes=[str(_hash_with_n_bits_set(32))],
    )
    defaults.update(overrides)
    return GeoIntegrityInput(**defaults)


class TestGpsAccuracy:
    @pytest.mark.parametrize(
        "acc,expected_points,expected_passed",
        [
            (10.0, 8, True),
            (10.01, 4, False),
            (25.0, 4, False),
            (25.01, 0, False),
            (None, 0, False),
        ],
    )
    def test_bands(self, acc, expected_points, expected_passed):
        result = evaluate(_base_input(gps_accuracy_m=acc))
        flag = _flag(result, RULE_GPS_ACCURACY)
        assert flag.points == expected_points
        assert flag.passed is expected_passed
        assert flag.max == 8


class TestInsideBoundary:
    def test_inside_passes(self):
        result = evaluate(_base_input())
        flag = _flag(result, RULE_INSIDE_BOUNDARY)
        assert flag.passed is True
        assert flag.points == 8

    def test_outside_fails(self):
        result = evaluate(
            _base_input(
                lat=OUTSIDE_LAT,
                lon=OUTSIDE_LON,
                photo1_exif=ExifData(
                    gps=(OUTSIDE_LAT, OUTSIDE_LON), captured_at=dt.datetime(2025, 2, 1, 9, 0, 0)
                ),
            )
        )
        flag = _flag(result, RULE_INSIDE_BOUNDARY)
        assert flag.passed is False
        assert flag.points == 0

    def test_on_edge_not_contained(self):
        # shapely .contains() excludes boundary-touching points, same as ST_Contains
        result = evaluate(_base_input(lat=25.95, lon=92.00))
        flag = _flag(result, RULE_INSIDE_BOUNDARY)
        assert flag.passed is False


class TestExifConsistency:
    def test_full_match(self):
        result = evaluate(_base_input())
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 6
        assert flag.passed is True

    def test_only_gps_present(self):
        result = evaluate(_base_input(photo1_exif=ExifData(gps=(INSIDE_LAT, INSIDE_LON), captured_at=None)))
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 3
        assert flag.passed is False

    def test_only_timestamp_present(self):
        result = evaluate(
            _base_input(photo1_exif=ExifData(gps=None, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0)))
        )
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 3

    def test_both_present_only_gps_matches(self):
        result = evaluate(
            _base_input(
                photo1_exif=ExifData(
                    gps=(INSIDE_LAT, INSIDE_LON), captured_at=dt.datetime(2020, 1, 1, 9, 0, 0)
                )
            )
        )
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 3

    def test_both_present_only_timestamp_matches(self):
        result = evaluate(
            _base_input(photo1_exif=ExifData(gps=(0.0, 0.0), captured_at=dt.datetime(2025, 2, 1, 9, 0, 0)))
        )
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 3

    def test_none_present_missing_exif(self):
        result = evaluate(_base_input(photo1_exif=ExifData(gps=None, captured_at=None)))
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 0
        assert flag.passed is False

    def test_no_exif_object_at_all(self):
        result = evaluate(_base_input(photo1_exif=None))
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 0

    def test_both_present_neither_matches(self):
        result = evaluate(
            _base_input(photo1_exif=ExifData(gps=(0.0, 0.0), captured_at=dt.datetime(2020, 1, 1, 9, 0, 0)))
        )
        flag = _flag(result, RULE_EXIF_CONSISTENCY)
        assert flag.points == 0


class TestDuplicatePhoto:
    def test_far_hash_passes(self):
        result = evaluate(
            _base_input(
                photo1_phash=str(_hash_with_n_bits_set(0)), existing_phashes=[str(_hash_with_n_bits_set(32))]
            )
        )
        flag = _flag(result, RULE_DUPLICATE_PHOTO)
        assert flag.passed is True
        assert flag.points == 5

    def test_identical_hash_fails(self):
        h = str(_hash_with_n_bits_set(10))
        result = evaluate(_base_input(photo1_phash=h, existing_phashes=[h]))
        flag = _flag(result, RULE_DUPLICATE_PHOTO)
        assert flag.passed is False
        assert flag.points == 0

    def test_hamming_distance_exactly_6_is_duplicate(self):
        base = _hash_with_n_bits_set(0)
        other = _hash_with_n_bits_set(6)  # differs from base in exactly 6 bits
        result = evaluate(_base_input(photo1_phash=str(base), existing_phashes=[str(other)]))
        flag = _flag(result, RULE_DUPLICATE_PHOTO)
        assert flag.points == 0  # distance == 6 is NOT > 6, so it counts as a duplicate

    def test_hamming_distance_7_passes(self):
        base = _hash_with_n_bits_set(0)
        other = _hash_with_n_bits_set(7)
        result = evaluate(_base_input(photo1_phash=str(base), existing_phashes=[str(other)]))
        flag = _flag(result, RULE_DUPLICATE_PHOTO)
        assert flag.points == 5

    def test_no_existing_photos_passes(self):
        result = evaluate(_base_input(existing_phashes=[]))
        flag = _flag(result, RULE_DUPLICATE_PHOTO)
        assert flag.points == 5


class TestTimestampSane:
    def test_within_window_passes(self):
        result = evaluate(_base_input())
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.passed is True
        assert flag.points == 3

    def test_before_window_fails(self):
        result = evaluate(_base_input(captured_at=dt.datetime(2022, 1, 1, tzinfo=dt.UTC)))
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.points == 0

    def test_after_window_fails(self):
        result = evaluate(_base_input(captured_at=dt.datetime(2025, 6, 1, tzinfo=dt.UTC)))
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.points == 0

    def test_future_dated_fails(self):
        result = evaluate(_base_input(captured_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC)))
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.points == 0

    def test_missing_fails(self):
        result = evaluate(_base_input(captured_at=None))
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.points == 0

    def test_missing_window_bounds_only_checks_future(self):
        result = evaluate(
            _base_input(
                window_start=None,
                window_end=None,
                captured_at=dt.datetime(2019, 1, 1, tzinfo=dt.UTC),
            )
        )
        flag = _flag(result, RULE_TIMESTAMP_SANE)
        assert flag.points == 3


class TestAggregation:
    def test_all_pass_sums_to_30(self):
        result = evaluate(_base_input())
        assert result.geo_score == 30
        assert len(result.geo_flags) == 5
        assert {f.rule for f in result.geo_flags} == {
            RULE_GPS_ACCURACY,
            RULE_INSIDE_BOUNDARY,
            RULE_EXIF_CONSISTENCY,
            RULE_DUPLICATE_PHOTO,
            RULE_TIMESTAMP_SANE,
        }

    def test_all_fail_sums_to_0(self):
        dup_hash = str(_hash_with_n_bits_set(10))
        result = evaluate(
            _base_input(
                gps_accuracy_m=None,
                lat=OUTSIDE_LAT,
                lon=OUTSIDE_LON,
                photo1_exif=ExifData(gps=None, captured_at=None),
                photo1_phash=dup_hash,
                existing_phashes=[dup_hash],
                captured_at=None,
            )
        )
        assert result.geo_score == 0
