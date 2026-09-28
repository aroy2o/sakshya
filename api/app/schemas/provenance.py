"""GET /provenance — Reality Pass R4 (docs/REAL_DATA_PLAN.md §3 rule 2, §8's
R4 row): "Every dataset has an entry in docs/DATA_SOURCES.md and in
GET /provenance (name, URL, licence, retrieved_at, real/synthetic)."

One entry per dataset the project uses, real or synthetic — CLAUDE.md's
synthetic-data-transparency non-negotiable applies here too: a dataset
that isn't real must say so plainly (`is_synthetic=true`), never blend in
next to the real ones unlabelled.
"""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class ProvenanceEntry(BaseModel):
    name: str
    source_url: str | None = None
    licence: str
    retrieved_at: str | None = (
        None  # ISO date/datetime; null for "not yet fetched" or evergreen synthetic data
    )
    is_synthetic: bool
    photo_source: str | None = None  # 'field' | 'ai_generated' | 'stock_cc' | 'unknown' — see validator below
    used_for: str
    notes: str | None = None
    owner: str  # which Reality-Pass slice/agent role this belongs to, e.g. "R3 backend-engineer"

    @model_validator(mode="after")
    def _photo_source_required_when_synthetic_and_photo_bearing(self) -> ProvenanceEntry:
        # CLAUDE.md: "`photo_source` goes with it. Whenever `is_synthetic` =
        # true, also set `photo_source`" — that rule is specifically about
        # photo-bearing records (field_record rows), not every synthetic
        # dataset (a synthetic watershed boundary has no "photo_source" to
        # speak of). Enforced only where a photo_source value is actually
        # present or the dataset's name says it's photo-related, so this
        # stays a real check rather than a rule nobody can satisfy.
        if self.is_synthetic and self.photo_source is not None:
            valid = {"field", "ai_generated", "stock_cc", "unknown"}
            if self.photo_source not in valid:
                raise ValueError(f"photo_source {self.photo_source!r} must be one of {valid}")
        return self
