"""GET /mws/{id}/assets, GET /assets/{id}, POST /assets/{id}/classify (FR2.2),
POST /assets/{id}/satellite (FR3.4) — PRD §9.

classify/satellite both follow the same shape: find the record + its
asset_evidence row, ingest a result from elsewhere (vision-ai-engineer's
classifier / geospatial-engineer's precomputed satellite results), persist
the JSONB blob + its INT sub-score, return the full updated asset detail.
Neither ever calls a live external service from this request path
(precompute-first non-negotiable) - the vision call goes through
MockVisionProvider (no live API key exists yet), and satellite data is read
from geospatial-engineer's already-precomputed output files, never GEE.
"""

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
from app.services import geospatial_output, photo_service
from app.services.vision import get_vision_classifier_service

router = APIRouter(tags=["assets"])


def _to_asset_detail(record: FieldRecord, evidence: AssetEvidence | None) -> AssetDetailOut:
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


def _get_record_and_evidence(asset_id: int, db: Session) -> tuple[FieldRecord, AssetEvidence | None]:
    row = db.execute(
        select(FieldRecord, AssetEvidence)
        .join(AssetEvidence, AssetEvidence.record_id == FieldRecord.id, isouter=True)
        .where(FieldRecord.id == asset_id)
    ).first()
    if row is None:
        raise HTTPException(404, f"asset {asset_id} not found")
    return row[0], row[1]


@router.get("/assets/{asset_id}", response_model=AssetDetailOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> AssetDetailOut:
    record, evidence = _get_record_and_evidence(asset_id, db)
    return _to_asset_detail(record, evidence)


@router.post("/assets/{asset_id}/classify", response_model=AssetDetailOut)
def classify_asset(asset_id: int, db: Session = Depends(get_db)) -> AssetDetailOut:
    """FR2.2 — run vision-ai-engineer's classifier against this asset's
    photo1, persist ai_result + visual_score. Re-running overwrites the
    previous classification (PRD §9: "Run/re-run")."""
    record, evidence = _get_record_and_evidence(asset_id, db)
    if evidence is None:
        raise HTTPException(500, f"asset {asset_id} has no asset_evidence row (should be created at ingest)")
    if not record.photo1_url:
        raise HTTPException(422, f"asset {asset_id} has no photo1_url to classify")

    local_path = photo_service.resolve_local_path(record.photo1_url)
    if not local_path.exists():
        raise HTTPException(422, f"photo1 file not found on disk at {local_path}")

    service = get_vision_classifier_service()
    outcome = service.classify(local_path, record.category, record.activity)

    evidence.ai_result = outcome.ai_result
    evidence.visual_score = outcome.visual_score
    db.commit()
    db.refresh(evidence)
    return _to_asset_detail(record, evidence)


@router.post("/assets/{asset_id}/satellite", response_model=AssetDetailOut)
def ingest_satellite_result(asset_id: int, db: Session = Depends(get_db)) -> AssetDetailOut:
    """FR3.4 — ingest geospatial-engineer's precomputed per-record satellite
    result (scripts/output/{mws_id}/satellite_results.json) into
    asset_evidence.sat_result + satellite_score. Never calls Earth Engine or
    computes anything here - geospatial-engineer's offline script already did
    the DiD scoring per PRD §12.3; this just persists it."""
    record, evidence = _get_record_and_evidence(asset_id, db)
    if evidence is None:
        raise HTTPException(500, f"asset {asset_id} has no asset_evidence row (should be created at ingest)")

    try:
        results = geospatial_output.load_satellite_results(record.mws_id)
    except FileNotFoundError:
        raise HTTPException(404, f"no precomputed satellite results for mws {record.mws_id!r} yet") from None

    match = next((r for r in results if r.get("record_id") == asset_id), None)
    if match is None:
        raise HTTPException(404, f"no precomputed satellite result found for asset {asset_id}")

    satellite_score = match.get("satellite_score")
    if not isinstance(satellite_score, int):
        raise HTTPException(
            500, f"precomputed result for asset {asset_id} is missing a valid integer satellite_score"
        )

    evidence.sat_result = match
    evidence.satellite_score = satellite_score
    db.commit()
    db.refresh(evidence)
    return _to_asset_detail(record, evidence)
