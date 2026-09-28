from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoJSONGeometry


class MWSCreate(BaseModel):
    id: str
    name: str | None = None
    project_id: str | None = None
    state: str | None = None
    district: str | None = None
    boundary: GeoJSONGeometry
    baseline_start: dt.date | None = None
    baseline_end: dt.date | None = None
    latest_start: dt.date | None = None
    latest_end: dt.date | None = None
    is_synthetic_boundary: bool = False


class MWSSummary(BaseModel):
    id: str
    name: str | None
    project_id: str | None
    state: str | None
    district: str | None
    baseline_start: dt.date | None
    baseline_end: dt.date | None
    latest_start: dt.date | None
    latest_end: dt.date | None
    is_synthetic_boundary: bool
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class MWSStats(BaseModel):
    """Field names match frontend-engineer's approved mock exactly (band
    names used directly as keys, no `_count` suffix) per sync-point
    reconciliation — PRD §9 names "summary stats" without specifying fields."""

    total_assets: int
    verified: int
    review: int
    flag: int
    unscored: int


class MWSDetail(MWSSummary):
    boundary: dict[str, Any]
    stats: MWSStats
