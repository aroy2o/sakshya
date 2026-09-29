"""GET /mws/{id}/watershed-impact — Reality Pass R2 (docs/REAL_DATA_PLAN.md §4).

Serves geospatial-engineer's precomputed watershed-level matched-control
bootstrap DiD (scripts/precompute_watershed_timeseries.py's output) - never
calls Earth Engine live (precompute-first non-negotiable, CLAUDE.md). Both
files carry their own top-level `placeholder`/`source` fields (same
convention as satellite_results.json and the thematic manifest); this router
passes them through untouched rather than collapsing them into one flag, so
a consumer can tell summary and timeseries apart if they ever diverge.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import get_db
from app.models.mws import COLLECTION as MWS_COLLECTION
from app.schemas.watershed_impact import WatershedImpactOut
from app.services import geospatial_output

router = APIRouter(tags=["watershed-impact"])


@router.get("/mws/{mws_id}/watershed-impact", response_model=WatershedImpactOut)
def get_watershed_impact(mws_id: str, db: Database = Depends(get_db)) -> WatershedImpactOut:
    if db[MWS_COLLECTION].find_one({"_id": mws_id}, {"_id": 1}) is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")

    try:
        summary = geospatial_output.load_watershed_did_summary(mws_id)
    except FileNotFoundError:
        raise HTTPException(404, f"no precomputed watershed-impact summary for mws {mws_id!r} yet") from None

    try:
        timeseries = geospatial_output.load_watershed_timeseries(mws_id)
    except FileNotFoundError:
        raise HTTPException(404, f"no precomputed watershed-impact timeseries for mws {mws_id!r} yet") from None

    return WatershedImpactOut(mws_id=mws_id, summary=summary, timeseries=timeseries)
