"""Shared pytest fixtures.

Two tiers, deliberately kept separate:
  * Pure unit tests (test_geo_integrity.py) touch no fixture here that needs
    a DB - they never trigger a migration or a live Postgres connection.
  * Integration tests (test_mws_api.py, test_records_api.py) request the
    `client` fixture, which lazily runs `alembic upgrade head` against
    DATABASE_URL_TEST (once per test session) before yielding a TestClient,
    and truncates all tables after every test.

Env vars MUST be set before the first `from app...` import anywhere in this
process, since app.config.get_settings() is evaluated at module-import time
in app/db.py and app/services/photo_service.py.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from shapely.geometry import Polygon

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL_TEST", "postgresql+psycopg2://sakshya:sakshya@localhost:5433/sakshya_test"
)
TEST_PHOTO_DIR = API_ROOT / "tests" / "_tmp_photos"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DATABASE_URL_TEST"] = TEST_DATABASE_URL
os.environ["PHOTO_STORAGE_DIR"] = str(TEST_PHOTO_DIR)
os.environ.setdefault("PHOTO_PUBLIC_BASE_URL", "http://testserver/static/photos")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _migrated_db():
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(API_ROOT), check=True)
    TEST_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(TEST_PHOTO_DIR, ignore_errors=True)


@pytest.fixture
def client(_migrated_db):
    with TestClient(app) as test_client:
        yield test_client
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE asset_evidence, field_record, mws CASCADE"))


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
