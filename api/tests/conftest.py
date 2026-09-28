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

from fastapi.testclient import TestClient  # noqa: E402

from app.db import _db as mongo_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_dirs():
    TEST_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(TEST_PHOTO_DIR, ignore_errors=True)
    shutil.rmtree(TEST_GEOSPATIAL_DIR, ignore_errors=True)


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

    def _write(mws_id: str, *, satellite_results: list[dict] | None = None) -> Path:
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

        return mws_dir

    return _write
