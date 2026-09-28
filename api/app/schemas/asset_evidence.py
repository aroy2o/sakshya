from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel


class AssetDetailOut(BaseModel):
    """GET /assets/{id} - field_record columns + full asset_evidence breakdown.

    Phase 1 only ever populates geo_flags/geo_score; everything from
    ai_result onward stays null until Phase 2/3/4 wire in (never faked)."""

    # field_record
    id: int
    work_code: str | None
    mws_id: str
    category: str
    activity: str
    status: str | None
    lat: float
    lon: float
    gps_accuracy_m: float | None
    orientation: float | None
    captured_at: dt.datetime | None
    photo1_url: str | None
    photo2_url: str | None
    photo1_phash: str | None
    photo2_phash: str | None
    remarks: str | None
    observer_id: str | None
    observer_name: str | None
    organisation: str | None
    is_synthetic: bool
    photo_source: str | None
    created_at: dt.datetime

    # asset_evidence
    geo_flags: list[dict[str, Any]] | None
    geo_score: int | None
    ai_result: dict[str, Any] | None
    visual_score: int | None
    sat_result: dict[str, Any] | None
    satellite_score: int | None
    temporal_score: int | None
    evidence_score: int | None
    band: str | None
    reviewer_decision: str | None
    reviewed_at: dt.datetime | None
    scored_at: dt.datetime | None
