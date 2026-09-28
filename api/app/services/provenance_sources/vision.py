"""Provenance entries owned by vision-ai-engineer (Reality Pass R5 — the
real-photo classifier benchmark: >=20 CC-licensed real photos with
per-file URL/author/licence, run against the current model + one
alternative, measured accuracy exposed via the API).

vision-ai-engineer: add your entries to ENTRIES below as they land (the
benchmark photo set's source/licence, and — once measured — where the
real-world accuracy number is exposed). Until R5 lands, this stays an
empty list rather than a guessed/fabricated entry (CLAUDE.md: never
fabricate a number/entry).

See app/services/provenance_sources/__init__.py for how this fits into
GET /provenance, and app/schemas/provenance.py for the entry shape.
"""

from __future__ import annotations

from app.schemas.provenance import ProvenanceEntry

ENTRIES: list[ProvenanceEntry] = []
