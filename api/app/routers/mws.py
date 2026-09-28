"""POST /mws, GET /mws, GET /mws/{id} — PRD §9.

Response shapes are unchanged by the Postgres->Mongo storage swap (byte-for-
byte identical, per the coordinator's explicit instruction) - only how they
get fetched/stored changed.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from shapely.geometry import MultiPolygon, mapping, shape

from app.db import get_db
from app.models.field_record import COLLECTION as FIELD_RECORD_COLLECTION
from app.models.mws import COLLECTION as MWS_COLLECTION
from app.schemas.mws import MWSCreate, MWSDetail, MWSStats, MWSSummary

router = APIRouter(tags=["mws"])


def _coerce_multipolygon(boundary) -> MultiPolygon:
    geom = shape(boundary.model_dump())
    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    if geom.geom_type == "MultiPolygon":
        return geom
    raise HTTPException(422, f"boundary must be Polygon or MultiPolygon, got {geom.geom_type}")


def _iso_date(value: dt.date | None) -> str | None:
    return value.isoformat() if value else None


def _stats_for(mws_id: str, db: Database) -> MWSStats:
    ids = [doc["_id"] for doc in db[FIELD_RECORD_COLLECTION].find({"mws_id": mws_id}, {"_id": 1})]
    total = len(ids)
    band_counts: dict[str, int] = {}
    if ids:
        for evidence in db.asset_evidence.find({"_id": {"$in": ids}}, {"band": 1}):
            band = evidence.get("band")
            if band:
                band_counts[band] = band_counts.get(band, 0) + 1
    verified = band_counts.get("verified", 0)
    review = band_counts.get("review", 0)
    flag = band_counts.get("flag", 0)
    unscored = total - verified - review - flag
    return MWSStats(total_assets=total, verified=verified, review=review, flag=flag, unscored=unscored)


def _to_detail(doc: dict, db: Database) -> MWSDetail:
    return MWSDetail(
        id=doc["_id"],
        name=doc.get("name"),
        project_id=doc.get("project_id"),
        state=doc.get("state"),
        district=doc.get("district"),
        baseline_start=doc.get("baseline_start"),
        baseline_end=doc.get("baseline_end"),
        latest_start=doc.get("latest_start"),
        latest_end=doc.get("latest_end"),
        is_synthetic_boundary=doc.get("is_synthetic_boundary", False),
        boundary_source=doc.get("boundary_source"),
        created_at=doc["created_at"],
        boundary=doc["geom"],  # already the exact GeoJSON dict stored at insert time
        stats=_stats_for(doc["_id"], db),
    )


def _to_summary(doc: dict) -> MWSSummary:
    return MWSSummary(
        id=doc["_id"],
        name=doc.get("name"),
        project_id=doc.get("project_id"),
        state=doc.get("state"),
        district=doc.get("district"),
        boundary_source=doc.get("boundary_source"),
        baseline_start=doc.get("baseline_start"),
        baseline_end=doc.get("baseline_end"),
        latest_start=doc.get("latest_start"),
        latest_end=doc.get("latest_end"),
        is_synthetic_boundary=doc.get("is_synthetic_boundary", False),
        created_at=doc["created_at"],
    )


@router.post("/mws", response_model=MWSDetail, status_code=201)
def create_mws(payload: MWSCreate, db: Database = Depends(get_db)) -> MWSDetail:
    if db[MWS_COLLECTION].find_one({"_id": payload.id}, {"_id": 1}) is not None:
        raise HTTPException(409, f"mws {payload.id!r} already exists")

    geom = _coerce_multipolygon(payload.boundary)
    doc = {
        "_id": payload.id,
        "name": payload.name,
        "project_id": payload.project_id,
        "state": payload.state,
        "district": payload.district,
        "geom": mapping(geom),
        "baseline_start": _iso_date(payload.baseline_start),
        "baseline_end": _iso_date(payload.baseline_end),
        "latest_start": _iso_date(payload.latest_start),
        "latest_end": _iso_date(payload.latest_end),
        "is_synthetic_boundary": payload.is_synthetic_boundary,
        "created_at": dt.datetime.now(dt.UTC),
    }
    try:
        db[MWS_COLLECTION].insert_one(doc)
    except DuplicateKeyError:
        # Race between the pre-check above and this insert - _id's uniqueness
        # constraint (Mongo enforces this on every collection's _id for free)
        # is the actual source of truth; the find_one above is just a
        # friendlier error message in the common (non-racing) case.
        raise HTTPException(409, f"mws {payload.id!r} already exists") from None
    return _to_detail(doc, db)


@router.get("/mws", response_model=list[MWSSummary])
def list_mws(db: Database = Depends(get_db)) -> list[MWSSummary]:
    docs = db[MWS_COLLECTION].find({}, {"geom": 0}).sort("created_at", 1)
    return [_to_summary(doc) for doc in docs]


@router.get("/mws/{mws_id}", response_model=MWSDetail)
def get_mws(mws_id: str, db: Database = Depends(get_db)) -> MWSDetail:
    doc = db[MWS_COLLECTION].find_one({"_id": mws_id})
    if doc is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")
    return _to_detail(doc, db)
