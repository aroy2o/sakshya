"""mws collection — PRD.md §8 (Mongo variant, see the proposed rewrite handed
to the coordinator alongside this change). Demo uses HydroBASINS L12 as a
stand-in for official MWS polygons; see `is_synthetic_boundary`.

No ORM here (Mongo is schemaless) — this module is documentation + a stable
import point for the collection name, matching the previous SQLAlchemy
module's role of "this is what the shape means," just without the class.

Document shape::

    {
        "_id": str,                    # e.g. HYBAS_ID - what the API calls `id`
        "name": str | None,
        "project_id": str | None,
        "state": str | None,
        "district": str | None,
        "geom": dict,                   # GeoJSON MultiPolygon (2dsphere-indexed)
        "baseline_start": str | None,   # ISO date "YYYY-MM-DD"
        "baseline_end": str | None,
        "latest_start": str | None,
        "latest_end": str | None,
        "is_synthetic_boundary": bool,
        "created_at": datetime,
    }
"""

from __future__ import annotations

COLLECTION = "mws"
