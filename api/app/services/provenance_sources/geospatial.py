"""Provenance entries owned by geospatial-engineer (Reality Pass R1 — real
SLUSI micro-watershed / LGD district boundaries, and R2 — real Earth Engine
DiD/time-series satellite analysis with matched controls).

geospatial-engineer: add your entries to ENTRIES below as they land (real
boundary source, real satellite analysis parameters/inputs). Until R1/R2
land, this stays an empty list rather than a guessed/fabricated entry
(CLAUDE.md: never fabricate a number/entry — an honestly-empty list is
correct here, not a placeholder row pretending to be real data).

See app/services/provenance_sources/__init__.py for how this fits into
GET /provenance, and app/schemas/provenance.py for the entry shape.
"""

from __future__ import annotations

from app.schemas.provenance import ProvenanceEntry

ENTRIES: list[ProvenanceEntry] = []
