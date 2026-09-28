"""MongoDB connection (switched from PostgreSQL+PostGIS per explicit human
decision, see CLAUDE.md "DB:" and PRD.md §8's proposed rewrite).

`get_db()` returns the pymongo `Database` directly (no per-request
session/connection object needed — `MongoClient` is a thread-safe, pooled
client meant to be created once and shared, same lifetime as the process).
`ensure_indexes()` is called once at app startup (app/main.py) since Mongo
has no migration tool: indexes are declared in code and created idempotently
on boot rather than via a separate migration step.
"""

from __future__ import annotations

from pymongo import ASCENDING, GEOSPHERE, MongoClient
from pymongo.database import Database

from app.config import get_settings

settings = get_settings()

# tz_aware=True: reads come back as timezone-aware UTC datetimes, matching
# what the Pydantic schemas (and geo_integrity's timestamp_sane rule, which
# compares captured_at against an aware `now`) expect.
_client: MongoClient = MongoClient(settings.mongo_uri, tz_aware=True)
_db: Database = _client.get_default_database()


def get_db() -> Database:
    return _db


def ensure_indexes() -> None:
    """Idempotent - safe to call on every startup. 2dsphere indexes are the
    Mongo equivalent of PostGIS's GiST indexes on geometry columns (FR1.2's
    `idx_mws_geom` / `idx_field_record_geom`), kept for future spatial
    queries even though geo_integrity.py's boundary check stays in-process
    Shapely (`.contains()`), not a live geospatial query, per this round's
    explicit instruction not to touch that module."""
    _db.mws.create_index([("geom", GEOSPHERE)])
    _db.field_record.create_index([("geom", GEOSPHERE)])
    _db.field_record.create_index([("mws_id", ASCENDING)])
    _db.asset_evidence.create_index([("band", ASCENDING)])
