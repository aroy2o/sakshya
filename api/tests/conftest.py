"""Shared pytest fixtures.

Two tiers, deliberately kept separate:
  * Pure unit tests (test_geo_integrity.py) touch no fixture here that needs
    a DB - they never open a Mongo connection.
  * Integration tests (test_mws_api.py, test_records_api.py, etc.) request
    the `client` fixture, which yields a TestClient against MONGO_URI_TEST
    and drops every collection after each test for isolation.

Env vars MUST be set before the first `from app...` import anywhere in this
process, since app.config.get_settings() is evaluated at module-import time
in app/db.py and app/services/photo_service.py.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest
from shapely.geometry import Polygon

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

TEST_MONGO_URI = os.environ.get("MONGO_URI_TEST", "mongodb://localhost:27018/sakshya_test")
TEST_PHOTO_DIR = API_ROOT / "tests" / "_tmp_photos"
TEST_GEOSPATIAL_DIR = API_ROOT / "tests" / "_tmp_geospatial"
TEST_REGISTRY_DIR = API_ROOT / "tests" / "_tmp_registry"
TEST_REAL_PHOTOS_DIR = API_ROOT / "tests" / "_tmp_real_photos"

os.environ["MONGO_URI"] = TEST_MONGO_URI
os.environ["MONGO_URI_TEST"] = TEST_MONGO_URI
os.environ["PHOTO_STORAGE_DIR"] = str(TEST_PHOTO_DIR)
os.environ.setdefault("PHOTO_PUBLIC_BASE_URL", "http://testserver/static/photos")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
# Isolated from geospatial-engineer's real scripts/output/ - tests write their
# own small fixtures here via the `geospatial_fixture` fixture below, so they
# never depend on (or get broken by changes to) the real precomputed output.
os.environ["GEOSPATIAL_OUTPUT_DIR"] = str(TEST_GEOSPATIAL_DIR)
os.environ.setdefault("THEMATIC_PUBLIC_BASE_URL", "http://testserver/static/geospatial")
# Isolated from the real scripts/output/registry/ (R3's fetch_gt2.py output)
# for the same reason as GEOSPATIAL_OUTPUT_DIR above - tests write their own
# small fixture via `programme_fixture` below.
os.environ["REGISTRY_OUTPUT_DIR"] = str(TEST_REGISTRY_DIR)
# Isolated from the real scripts/real_photos/ (R5's fetch_real_benchmark_photos.py
# + run_real_photo_benchmark.py output) for the same reason as
# REGISTRY_OUTPUT_DIR above - tests write their own small fixture via
# `real_photos_fixture` below.
os.environ["REAL_PHOTOS_OUTPUT_DIR"] = str(TEST_REAL_PHOTOS_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app.db import _db as mongo_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_dirs():
    TEST_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(TEST_PHOTO_DIR, ignore_errors=True)
    shutil.rmtree(TEST_GEOSPATIAL_DIR, ignore_errors=True)
    shutil.rmtree(TEST_REGISTRY_DIR, ignore_errors=True)
    shutil.rmtree(TEST_REAL_PHOTOS_DIR, ignore_errors=True)


@pytest.fixture
def client(_test_dirs):
    with TestClient(app) as test_client:
        yield test_client
    for collection_name in ("mws", "field_record", "asset_evidence", "counters"):
        mongo_db[collection_name].delete_many({})


@pytest.fixture
def boundary_polygon() -> Polygon:
    """~11km square centered near Morigaon, Assam - matches the placeholder
    watershed boundary used by the seed script."""
    return Polygon(
        [
            (91.95, 25.95),
            (92.05, 25.95),
            (92.05, 26.05),
            (91.95, 26.05),
            (91.95, 25.95),
        ]
    )


@pytest.fixture
def geospatial_fixture():
    """Factory for a minimal fake scripts/output/{mws_id}/ tree under
    TEST_GEOSPATIAL_DIR, so thematic/satellite endpoint tests are hermetic -
    they never depend on (or risk being broken by changes to)
    geospatial-engineer's real precomputed output."""
    import json

    from PIL import Image

    def _write(
        mws_id: str,
        *,
        satellite_results: list[dict] | None = None,
        watershed_did_summary: dict | None = None,
        watershed_timeseries: dict | None = None,
    ) -> Path:
        mws_dir = TEST_GEOSPATIAL_DIR / mws_id
        thematic_dir = mws_dir / "thematic"
        thematic_dir.mkdir(parents=True, exist_ok=True)

        Image.new("RGB", (4, 4), color=(10, 20, 30)).save(thematic_dir / "ndvi_before.png")
        (thematic_dir / "drainage.geojson").write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"strahler_order": 1},
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[92.28, 26.18], [92.30, 26.20]],
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        manifest = {
            "mws_id": mws_id,
            "placeholder": True,
            "layers": {
                "ndvi_before": {
                    "type": "raster_png",
                    "path": "ndvi_before.png",
                    "bounds": [92.28, 26.18, 92.30, 26.20],
                    "placeholder": True,
                },
                "drainage": {"type": "geojson", "path": "drainage.geojson", "placeholder": True},
            },
            "supporting_artifacts": {},
        }
        (thematic_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        if satellite_results is not None:
            (mws_dir / "satellite_results.json").write_text(json.dumps(satellite_results), encoding="utf-8")

        if watershed_did_summary is not None:
            (mws_dir / "watershed_did_summary.json").write_text(
                json.dumps(watershed_did_summary), encoding="utf-8"
            )

        if watershed_timeseries is not None:
            (mws_dir / "watershed_timeseries.json").write_text(json.dumps(watershed_timeseries), encoding="utf-8")

        return mws_dir

    return _write


@pytest.fixture
def programme_fixture():
    """Writes a small fake scripts/output/registry/programme_marigaon.json
    under TEST_REGISTRY_DIR, matching the exact shape
    scripts/fetch_gt2.py's `build_programme_summary()` produces - so
    GET /programme/marigaon tests are hermetic and never depend on (or risk
    being broken by re-running) the real R3 fetch against the live
    government site."""
    import json

    def _write(**overrides) -> Path:
        TEST_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "district": "Morigaon",
            "district_source_spelling": "MARIGAON",
            "state": "Assam",
            "district_total_projects": 2,
            "district_total_work_codes": 309,
            "district_geotagged_work_codes": 267,
            "district_non_geotagged_work_codes": 42,
            "projects": [
                {
                    "project_id": 90,
                    "project_name": "MARIGAON-WDC - 1 /2021-22",
                    "nrm_total": 73,
                    "epa_total": 11,
                    "livelihood_total": 112,
                    "production_total": 67,
                    "total_work_codes": 263,
                    "geotagged_work_codes": 240,
                    "non_geotagged_work_codes": 23,
                },
                {
                    "project_id": 1278,
                    "project_name": "MARIGAON-WDC - 2 /2025-26",
                    "nrm_total": 42,
                    "epa_total": 4,
                    "livelihood_total": 0,
                    "production_total": 0,
                    "total_work_codes": 46,
                    "geotagged_work_codes": 27,
                    "non_geotagged_work_codes": 19,
                },
            ],
            "focus_project": {
                "project_id": 90,
                "project_name": "MARIGAON-WDC - 1 /2021-22",
                "nrm_total": 73,
                "epa_total": 11,
                "livelihood_total": 112,
                "production_total": 67,
                "total_work_codes": 263,
                "geotagged_work_codes": 240,
                "non_geotagged_work_codes": 23,
                "note": "fixture note",
            },
            "category_breakdown": [
                {"category": "PT", "work_code_count": 23, "share_pct_of_geotagged": 9.6},
                {"category": "LS", "work_code_count": 92, "share_pct_of_geotagged": 38.3},
            ],
            "unmapped_activities": ["Rural Infrastructure"],
            "moderation_backlog": {
                "pre": {
                    "accepted": 109,
                    "yet_to_moderate": 123,
                    "rejected": 1,
                    "not_submitted": 6,
                    "mixed": 1,
                    "other": 0,
                    "yet_to_moderate_pct_of_geotagged": 51.2,
                },
                "mid": {
                    "accepted": 5,
                    "yet_to_moderate": 1,
                    "rejected": 0,
                    "not_submitted": 234,
                    "mixed": 0,
                    "other": 0,
                    "yet_to_moderate_pct_of_geotagged": 0.4,
                },
                "post": {
                    "accepted": 11,
                    "yet_to_moderate": 0,
                    "rejected": 0,
                    "not_submitted": 229,
                    "mixed": 0,
                    "other": 0,
                    "yet_to_moderate_pct_of_geotagged": 0.0,
                },
            },
            "moderation_backlog_denominator": 240,
            "moderation_backlog_note": "fixture note",
            "activity_category_mapping_source": "docs/REAL_DATA_PLAN.md §5",
            "source_report": "WDC-PMKSY 2.0 MIS, Report GT2 (Work Code Status with Geotagging Details)",
            "source_urls": {
                "work_code_detail": "https://wdcpmksy.dolr.gov.in/getProjDtlAssetGeoData?projid=90"
            },
            "retrieved_at": {"work_code_detail": "2026-09-28T10:25:58+00:00"},
            "is_synthetic": False,
        }
        data.update(overrides)
        (TEST_REGISTRY_DIR / "programme_marigaon.json").write_text(json.dumps(data), encoding="utf-8")
        return TEST_REGISTRY_DIR

    return _write


@pytest.fixture
def real_photos_fixture():
    """Writes a small fake scripts/real_photos/manifest.json +
    benchmark_summary_<model>.json under TEST_REAL_PHOTOS_DIR, matching the
    exact shapes scripts/fetch_real_benchmark_photos.py and
    scripts/run_real_photo_benchmark.py produce - so GET /classifier/benchmark
    tests are hermetic and never depend on (or risk being broken by
    re-running) the real Commons fetch / Ollama classification."""
    import json

    def _write(*, with_model_summary: bool = True) -> Path:
        TEST_REAL_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        manifest = [
            {
                "id": "real_001",
                "ground_truth_category": "SM",
                "commons_title": "File:Fixture check dam.jpg",
                "file_page_url": "https://commons.wikimedia.org/wiki/File:Fixture_check_dam.jpg",
                "image_url": "https://upload.wikimedia.org/fixture.jpg",
                "local_path": "scripts/real_photos/SM/fixture.jpg",
                "author": "Fixture Author",
                "license_short": "CC BY-SA 4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
                "credit": None,
                "description": "fixture",
                "width": 800,
                "height": 600,
                "downloaded_bytes": 12345,
                "retrieved_at": "2026-09-28T10:00:00+00:00",
                "source": "Wikimedia Commons",
            },
            {
                "id": "real_002",
                "ground_truth_category": "NONE",
                "commons_title": "File:Fixture bus.jpg",
                "file_page_url": "https://commons.wikimedia.org/wiki/File:Fixture_bus.jpg",
                "image_url": "https://upload.wikimedia.org/fixture2.jpg",
                "local_path": "scripts/real_photos/NONE/fixture2.jpg",
                "author": "Fixture Author 2",
                "license_short": "CC BY 2.0",
                "license_url": "https://creativecommons.org/licenses/by/2.0",
                "credit": None,
                "description": "fixture distractor",
                "width": 800,
                "height": 600,
                "downloaded_bytes": 6789,
                "retrieved_at": "2026-09-28T10:00:00+00:00",
                "source": "Wikimedia Commons",
            },
        ]
        (TEST_REAL_PHOTOS_DIR / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        if with_model_summary:
            summary = {
                "model": "moondream",
                "provider": "ollama",
                "n_photos": 2,
                "n_correct": 1,
                "n_errors": 0,
                "accuracy": 0.5,
                "axis_labels": ["AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM", "UNKNOWN"],
                "confusion_matrix": {"SM": {"SM": 1}, "UNKNOWN": {"PT": 1}},
                "neutral_declared_category": "UNKNOWN",
                "neutral_declared_activity": "unspecified activity (real-photo benchmark)",
                "generated_at": "2026-09-28T11:00:00+00:00",
                "note": "fixture note - measured on REAL photos, not the synthetic set",
            }
            (TEST_REAL_PHOTOS_DIR / "benchmark_summary_moondream.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
        return TEST_REAL_PHOTOS_DIR

    return _write
