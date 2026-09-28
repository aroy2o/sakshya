"""GET /mws/{id}/assets, GET /assets/{id} — PRD §9."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.asset_evidence import AssetEvidence
from app.models.field_record import FieldRecord
from app.models.mws import MWS
from app.schemas.asset_evidence import AssetDetailOut
from app.schemas.common import AssetFeature, AssetFeatureCollection, AssetFeatureProperties

router = APIRouter(tags=["assets"])


@router.get("/mws/{mws_id}/assets", response_model=AssetFeatureCollection)
def list_mws_assets(mws_id: str, db: Session = Depends(get_db)) -> AssetFeatureCollection:
    if db.get(MWS, mws_id) is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")

    rows = db.execute(
        select(FieldRecord, AssetEvidence.evidence_score, AssetEvidence.band)
        .join(AssetEvidence, AssetEvidence.record_id == FieldRecord.id, isouter=True)
        .where(FieldRecord.mws_id == mws_id)
    ).all()

    features = [
        AssetFeature(
            geometry=mapping(to_shape(record.geom)),
            properties=AssetFeatureProperties(
                id=record.id,
                work_code=record.work_code,
                category=record.category,
                activity=record.activity,
                status=record.status,
                captured_at=record.captured_at,
                photo1_url=record.photo1_url,
                is_synthetic=record.is_synthetic,
                evidence_score=evidence_score,
                band=band,
            ),
        )
        for record, evidence_score, band in rows
    ]
    return AssetFeatureCollection(features=features)


@router.get("/assets/{asset_id}", response_model=AssetDetailOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> AssetDetailOut:
    row = db.execute(
        select(FieldRecord, AssetEvidence)
        .join(AssetEvidence, AssetEvidence.record_id == FieldRecord.id, isouter=True)
        .where(FieldRecord.id == asset_id)
    ).first()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")
    record, evidence = row

    return AssetDetailOut(
        id=record.id,
        work_code=record.work_code,
        mws_id=record.mws_id,
        category=record.category,
        activity=record.activity,
        status=record.status,
        lat=record.lat,
        lon=record.lon,
        gps_accuracy_m=record.gps_accuracy_m,
        orientation=record.orientation,
        captured_at=record.captured_at,
        photo1_url=record.photo1_url,
        photo2_url=record.photo2_url,
        photo1_phash=record.photo1_phash,
        photo2_phash=record.photo2_phash,
        remarks=record.remarks,
        observer_id=record.observer_id,
        observer_name=record.observer_name,
        organisation=record.organisation,
        is_synthetic=record.is_synthetic,
        photo_source=record.photo_source,
        created_at=record.created_at,
        geo_flags=evidence.geo_flags if evidence else None,
        geo_score=evidence.geo_score if evidence else None,
        ai_result=evidence.ai_result if evidence else None,
        visual_score=evidence.visual_score if evidence else None,
        sat_result=evidence.sat_result if evidence else None,
        satellite_score=evidence.satellite_score if evidence else None,
        temporal_score=evidence.temporal_score if evidence else None,
        evidence_score=evidence.evidence_score if evidence else None,
        band=evidence.band if evidence else None,
        reviewer_decision=evidence.reviewer_decision if evidence else None,
        reviewed_at=evidence.reviewed_at if evidence else None,
        scored_at=evidence.scored_at if evidence else None,
    )
