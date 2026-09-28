"""POST /mws, GET /mws, GET /mws/{id} — PRD §9."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import MultiPolygon, mapping, shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.asset_evidence import AssetEvidence
from app.models.field_record import FieldRecord
from app.models.mws import MWS
from app.schemas.mws import MWSCreate, MWSDetail, MWSStats, MWSSummary

router = APIRouter(tags=["mws"])


def _coerce_multipolygon(boundary) -> MultiPolygon:
    geom = shape(boundary.model_dump())
    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    if geom.geom_type == "MultiPolygon":
        return geom
    raise HTTPException(422, f"boundary must be Polygon or MultiPolygon, got {geom.geom_type}")


def _stats_for(mws_id: str, db: Session) -> MWSStats:
    total = db.scalar(select(func.count()).select_from(FieldRecord).where(FieldRecord.mws_id == mws_id)) or 0
    band_counts = dict(
        db.execute(
            select(AssetEvidence.band, func.count())
            .join(FieldRecord, FieldRecord.id == AssetEvidence.record_id)
            .where(FieldRecord.mws_id == mws_id)
            .group_by(AssetEvidence.band)
        ).all()
    )
    verified = band_counts.get("verified", 0)
    review = band_counts.get("review", 0)
    flag = band_counts.get("flag", 0)
    unscored = total - verified - review - flag
    return MWSStats(total_assets=total, verified=verified, review=review, flag=flag, unscored=unscored)


def _to_detail(mws: MWS, db: Session) -> MWSDetail:
    boundary_geom = to_shape(mws.geom)
    return MWSDetail(
        id=mws.id,
        name=mws.name,
        project_id=mws.project_id,
        state=mws.state,
        district=mws.district,
        baseline_start=mws.baseline_start,
        baseline_end=mws.baseline_end,
        latest_start=mws.latest_start,
        latest_end=mws.latest_end,
        is_synthetic_boundary=mws.is_synthetic_boundary,
        created_at=mws.created_at,
        boundary=mapping(boundary_geom),
        stats=_stats_for(mws.id, db),
    )


@router.post("/mws", response_model=MWSDetail, status_code=201)
def create_mws(payload: MWSCreate, db: Session = Depends(get_db)) -> MWSDetail:
    if db.get(MWS, payload.id) is not None:
        raise HTTPException(409, f"mws {payload.id!r} already exists")

    geom = _coerce_multipolygon(payload.boundary)
    mws = MWS(
        id=payload.id,
        name=payload.name,
        project_id=payload.project_id,
        state=payload.state,
        district=payload.district,
        geom=from_shape(geom, srid=4326),
        baseline_start=payload.baseline_start,
        baseline_end=payload.baseline_end,
        latest_start=payload.latest_start,
        latest_end=payload.latest_end,
        is_synthetic_boundary=payload.is_synthetic_boundary,
    )
    db.add(mws)
    db.commit()
    db.refresh(mws)
    return _to_detail(mws, db)


@router.get("/mws", response_model=list[MWSSummary])
def list_mws(db: Session = Depends(get_db)) -> list[MWS]:
    return list(db.scalars(select(MWS).order_by(MWS.created_at)))


@router.get("/mws/{mws_id}", response_model=MWSDetail)
def get_mws(mws_id: str, db: Session = Depends(get_db)) -> MWSDetail:
    mws = db.get(MWS, mws_id)
    if mws is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")
    return _to_detail(mws, db)
