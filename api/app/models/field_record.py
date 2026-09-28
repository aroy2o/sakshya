"""field_record collection — PRD.md §8 (Mongo variant).

`is_synthetic`/`photo_source` are non-negotiable per CLAUDE.md: every
non-real record MUST have is_synthetic=true, and whenever it does,
photo_source MUST also be set (enforced in app/schemas/field_record.py's
Pydantic validator, unchanged by this storage swap).

`_id` is an app-assigned auto-incrementing int (see
app/services/sequences.py's `next_sequence()`), replacing Postgres's
`SERIAL PRIMARY KEY` — Mongo's ObjectId was deliberately not used here so the
API's `id: int` contract (GeoJSON feature properties, `/assets/{id}` path
params, frontend's zod schemas) stays byte-for-byte identical.

Document shape::

    {
        "_id": int,
        "work_code": str | None,
        "mws_id": str,
        "category": str,
        "activity": str,
        "status": str | None,
        "lat": float,
        "lon": float,
        "gps_accuracy_m": float | None,
        "orientation": float | None,
        "captured_at": datetime | None,
        "photo1_url": str | None,
        "photo2_url": str | None,
        "photo1_phash": str | None,
        "photo2_phash": str | None,
        "remarks": str | None,
        "observer_id": str | None,
        "observer_name": str | None,
        "organisation": str | None,
        "geom": dict,                # GeoJSON Point (2dsphere-indexed)
        "is_synthetic": bool,
        "photo_source": str | None,
        "created_at": datetime,
    }
"""

from __future__ import annotations

COLLECTION = "field_record"
