"""asset_evidence collection — PRD.md §8 (Mongo variant).

`_id` is the same int value as the owning field_record's `_id` (mirrors
Postgres's `record_id INT PRIMARY KEY REFERENCES field_record(id)` — a true
1:1 relationship keyed by the same value), so `db.asset_evidence.find_one({"_id": asset_id})`
is a direct O(1) lookup, no join needed for the single-asset case.

Phase 1 only ever populates geo_flags/geo_score; ai_result/visual_score
(Phase 2), sat_result/satellite_score (Phase 3), and evidence_score/band
(Phase 4) stay null until those phases wire in — never faked here.

Document shape::

    {
        "_id": int,                  # == owning field_record._id
        "geo_flags": list[dict] | None,
        "geo_score": int | None,
        "ai_result": dict | None,
        "visual_score": int | None,
        "sat_result": dict | None,
        "satellite_score": int | None,
        "temporal_score": int | None,
        "evidence_score": int | None,
        "band": str | None,
        "reviewer_decision": str | None,
        "reviewed_at": datetime | None,
        "scored_at": datetime | None,
    }
"""

from __future__ import annotations

COLLECTION = "asset_evidence"
