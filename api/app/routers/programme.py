"""GET /programme/marigaon — Reality Pass R3 (docs/REAL_DATA_PLAN.md §8's R3
row).

Serves scripts/fetch_gt2.py's precomputed WDC-PMKSY registry aggregates and
the exact (computed, not estimated) moderation backlog for the Marigaon
WDC-1 project. Static file read only, same pattern and same non-negotiable
as GET /mws/{id}/thematic/{layer}: never fetches wdcpmksy.dolr.gov.in live
from a request path (CLAUDE.md precompute-first).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.programme import ProgrammeMarigaonOut
from app.services import programme_registry

router = APIRouter(tags=["programme"])


@router.get("/programme/marigaon", response_model=ProgrammeMarigaonOut)
def get_programme_marigaon() -> ProgrammeMarigaonOut:
    try:
        data = programme_registry.load_programme_marigaon()
    except FileNotFoundError:
        raise HTTPException(
            404,
            "no precomputed programme registry yet - run scripts/fetch_gt2.py first",
        ) from None
    return ProgrammeMarigaonOut(**data)
