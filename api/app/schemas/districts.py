from __future__ import annotations

from pydantic import BaseModel, Field


class DistrictCoverageOut(BaseModel):
    """Matches web/src/schemas/domain.ts's zDistrictCoverage exactly:
    {district, state, total_works, geotagged_works, geotag_coverage_pct}.
    source_report/as_of are additive (silently stripped by zod's non-strict
    .parse() until frontend opts in to reading them) - see
    app/services/district_coverage.py for the real source citation."""

    district: str
    state: str
    total_works: int = Field(ge=0)
    geotagged_works: int = Field(ge=0)
    geotag_coverage_pct: float = Field(ge=0, le=100)
    source_report: str
    as_of: str
