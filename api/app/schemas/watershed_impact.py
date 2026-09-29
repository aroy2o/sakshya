"""GET /mws/{id}/watershed-impact — Reality Pass R2 (docs/REAL_DATA_PLAN.md §4).

Serves geospatial-engineer's precomputed watershed-level matched-control DiD
output verbatim - same "untyped passthrough, persist/serve exactly what the
offline script wrote" pattern as `sat_result`/`ai_result` (PRD §8), since the
shape is still evolving and re-typing it field-by-field here would just be a
second place to keep in sync. `summary`/`timeseries` are `dict[str, Any]` on
purpose, not because we don't care about the shape.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WatershedImpactOut(BaseModel):
    mws_id: str
    summary: dict[str, Any]
    timeseries: dict[str, Any]
