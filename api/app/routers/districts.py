"""GET /districts/geotag-coverage — PRD §9 / FR5.5.

Static table, per PRD §9's own wording ("entered manually or scraped once —
not live-scraped during demo") - no live network call from this request
path, ever. Real WDC-PMKSY MIS data; see app/services/district_coverage.py
for the full source citation and data-quality notes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.districts import DistrictCoverageOut
from app.services.district_coverage import get_district_coverage

router = APIRouter(tags=["districts"])


@router.get("/districts/geotag-coverage", response_model=list[DistrictCoverageOut])
def list_district_geotag_coverage() -> list[DistrictCoverageOut]:
    return [DistrictCoverageOut(**row) for row in get_district_coverage()]
