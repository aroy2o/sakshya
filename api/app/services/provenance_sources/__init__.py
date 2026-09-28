"""Aggregates every Reality-Pass provenance entry for GET /provenance (R4,
docs/REAL_DATA_PLAN.md §3 rule 2, §8's R4 row).

Split one module per owning Reality-Pass slice so concurrent agents never
edit the same file as each other:
  - backend.py     — R3 (work-code registry) + R4 (this endpoint itself,
                      district coverage) — backend-engineer
  - geospatial.py  — R1 (real MWS/district boundaries) + R2 (real Earth
                      Engine DiD/time-series analysis) — geospatial-engineer
  - vision.py      — R5 (real-photo classifier benchmark) — vision-ai-engineer

Add your own entries to YOUR OWN file as `ENTRIES: list[ProvenanceEntry]`
items. This `__init__` only imports and concatenates — it should never need
to change when a new dataset is added, only when a whole new module is.
"""

from __future__ import annotations

from app.schemas.provenance import ProvenanceEntry
from app.services.provenance_sources import backend, geospatial, vision

ALL_ENTRIES: list[ProvenanceEntry] = [
    *backend.ENTRIES,
    *geospatial.ENTRIES,
    *vision.ENTRIES,
]
