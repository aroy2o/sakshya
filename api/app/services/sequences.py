"""Auto-increment replacement for Postgres's `SERIAL` (field_record.id),
since Mongo has no built-in equivalent. Classic Mongo counters-collection
pattern: an atomic `find_one_and_update` with `$inc` — safe under concurrent
requests, same atomicity guarantee SERIAL gave for free.
"""

from __future__ import annotations

from pymongo import ReturnDocument
from pymongo.database import Database

COUNTERS_COLLECTION = "counters"


def next_sequence(db: Database, name: str) -> int:
    doc = db[COUNTERS_COLLECTION].find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]
