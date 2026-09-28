"""Per-record analysis output model — PRD.md §8.

Phase 1 only ever populates geo_flags/geo_score. ai_result/visual_score
(Phase 2), sat_result/satellite_score (Phase 3), and evidence_score/band
(Phase 4) stay null until those phases wire in — never faked here.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AssetEvidence(Base):
    __tablename__ = "asset_evidence"

    record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("field_record.id", ondelete="CASCADE"), primary_key=True
    )
    geo_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    geo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    visual_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sat_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    satellite_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temporal_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    band: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scored_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
