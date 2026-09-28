"""Provenance entries owned by vision-ai-engineer (Reality Pass R5 — the
real-photo classifier benchmark: >=20 CC-licensed real photos with
per-file URL/author/licence, run against the current model + one
alternative, measured accuracy exposed via the API).

45 real, CC-licensed photos hand-picked from Wikimedia Commons (individual
files, not a bulk category crawl — see scripts/fetch_real_benchmark_photos.py's
module docstring). Grouped here by ground-truth PRD §15.1 category, same
grouping as docs/DATA_SOURCES.md's "Photo/classifier benchmark" table — each
`licence` field below summarizes the licence variants actually present in
that group (never assumed uniform); full per-file author/licence/URL is in
scripts/real_photos/manifest.json, which `used_for` points back to.

Measured accuracy itself (confusion matrix, per model tested) is NOT
duplicated into ProvenanceEntry's flat shape here — that lives in the richer
GET /classifier/benchmark (api/app/routers/classifier_benchmark.py) and in
docs/CLASSIFIER_BENCHMARK.md. This file's entries are about the *dataset's*
provenance, matching what every other Reality-Pass module in this package
does (R1-R4 also don't put their computed results here, just source/licence).

See app/services/provenance_sources/__init__.py for how this fits into
GET /provenance, and app/schemas/provenance.py for the entry shape.
"""

from __future__ import annotations

from app.schemas.provenance import ProvenanceEntry

_MANIFEST_NOTE = (
    "Full per-file provenance (title, file_page_url, author, exact licence, retrieved_at) in "
    "scripts/real_photos/manifest.json. Methodology + confusion matrix + measured accuracy: "
    "docs/CLASSIFIER_BENCHMARK.md and GET /classifier/benchmark."
)

ENTRIES: list[ProvenanceEntry] = [
    ProvenanceEntry(
        name="Real-photo classifier benchmark — SM (Structural measures, check dams)",
        source_url="https://commons.wikimedia.org/wiki/Category:Check_dams_in_India",
        licence="CC BY-SA 3.0 / 4.0, CC0, Public domain (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (10 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — PT (Pond-Tanks)",
        source_url="https://commons.wikimedia.org/wiki/Category:Ponds_in_India",
        licence="CC BY-SA 3.0 / 4.0 (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (6 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — BN (Bunds)",
        source_url="https://commons.wikimedia.org/wiki/Category:Levees_in_India",
        licence="CC BY 3.0",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (5 photos)",
        notes="Baitarani river embankment restoration series, Odisha, one photographer. " + _MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — AM (Agronomic measures)",
        source_url="https://commons.wikimedia.org/wiki/Category:Agricultural_terraces_in_Kerala",
        licence="CC BY-SA 2.0 / 3.0 / 4.0 (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (5 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — VM (Vegetative measures)",
        source_url="https://commons.wikimedia.org/wiki/Category:Reforestation_in_India",
        licence="CC BY-SA 3.0 / 4.0 (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (3 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — LS (Livestock)",
        source_url="https://commons.wikimedia.org/wiki/Category:Goats_in_Assam",
        licence="CC BY-SA 4.0",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (3 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — LH (Livelihood)",
        source_url="https://commons.wikimedia.org/wiki/Category:Sericulture_in_India",
        licence="CC BY 4.0, CC BY-SA 3.0 / 4.0 (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (5 photos)",
        notes="Sericulture/handloom + fish-farming photos. " + _MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — NC (Nala-Channels)",
        source_url="https://commons.wikimedia.org/wiki/Category:Irrigation_canals_in_India",
        licence="CC BY 3.0, CC BY-SA 3.0 / 4.0, CC0 (varies per file)",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Real-photo classifier accuracy benchmark ground truth (5 photos)",
        notes=(
            "Small/village-scale channels only — major state infrastructure (Bhakra Main Canal, "
            "Sardar Sarovar, Narayanpur Right Bank Canal, Tungabhadra canal) deliberately excluded "
            "as a different scale from a watershed-programme nala/channel work. " + _MANIFEST_NOTE
        ),
        owner="R5 vision-ai-engineer",
    ),
    ProvenanceEntry(
        name="Real-photo classifier benchmark — NONE (deliberate distractors)",
        source_url="https://commons.wikimedia.org/wiki/Category:Street_markets_in_India",
        licence="CC BY-SA 4.0",
        retrieved_at="2026-09-28",
        is_synthetic=False,
        used_for="Tests whether the classifier over-predicts a PRD §15.1 category on an unrelated real scene (3 photos)",
        notes=_MANIFEST_NOTE,
        owner="R5 vision-ai-engineer",
    ),
]
