"""POST /records — PRD §9 / FR1.3.

Runs the geo-integrity validator synchronously and always ingests the record
regardless of how badly it fails geo-integrity: the whole point of
geo_score/bands/the Phase 6 review queue is to surface suspect records, not
silently drop them. Never calls a live vision/GEE service (precompute-first
non-negotiable) - only geo_score is populated here.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.asset_evidence import AssetEvidence
from app.models.field_record import FieldRecord
from app.models.mws import MWS
from app.schemas.common import GeoFlagOut
from app.schemas.field_record import FieldRecordIn, FieldRecordOut, GeoIntegrityOut, RecordIngestOut
from app.services import geo_integrity, photo_service

router = APIRouter(tags=["records"])


@router.post("/records", response_model=RecordIngestOut, status_code=201)
async def create_record(
    metadata: str = Form(..., description="JSON-encoded field-record metadata (see FieldRecordIn schema)"),
    photo1: UploadFile = File(..., description="Primary evidence photo - required"),
    photo2: UploadFile | None = File(None, description="Secondary photo - optional"),
    db: Session = Depends(get_db),
) -> RecordIngestOut:
    try:
        payload = FieldRecordIn.model_validate_json(metadata)
    except Exception as exc:  # pydantic ValidationError or JSON decode error
        raise HTTPException(422, f"invalid metadata JSON: {exc}") from exc

    mws = db.get(MWS, payload.mws_id)
    if mws is None:
        raise HTTPException(404, f"mws {payload.mws_id!r} not found")

    photo1_bytes = await photo1.read()
    if not photo1_bytes:
        raise HTTPException(422, "photo1 is required and must not be empty")
    photo2_bytes = await photo2.read() if photo2 is not None else None

    photo1_filename, photo1_url = photo_service.save_photo(photo1_bytes)
    photo1_phash = photo_service.compute_phash(photo1_bytes)
    photo1_exif = photo_service.extract_exif(photo1_bytes)

    photo2_url: str | None = None
    photo2_phash: str | None = None
    if photo2_bytes:
        _, photo2_url = photo_service.save_photo(photo2_bytes)
        photo2_phash = photo_service.compute_phash(photo2_bytes)

    existing_phashes = list(
        db.scalars(select(FieldRecord.photo1_phash).where(FieldRecord.photo1_phash.is_not(None)))
    ) + list(db.scalars(select(FieldRecord.photo2_phash).where(FieldRecord.photo2_phash.is_not(None))))

    boundary = to_shape(mws.geom)

    geo_input = geo_integrity.GeoIntegrityInput(
        lat=payload.lat,
        lon=payload.lon,
        gps_accuracy_m=payload.gps_accuracy_m,
        captured_at=payload.captured_at,
        boundary=boundary,
        window_start=mws.baseline_start,
        window_end=mws.latest_end,
        now=dt.datetime.now(dt.UTC),
        photo1_exif=photo1_exif,
        photo1_phash=photo1_phash,
        photo2_phash=photo2_phash,
        existing_phashes=existing_phashes,
    )
    result = geo_integrity.evaluate(geo_input)

    record = FieldRecord(
        work_code=payload.work_code,
        mws_id=payload.mws_id,
        category=payload.category,
        activity=payload.activity,
        status=payload.status,
        lat=payload.lat,
        lon=payload.lon,
        gps_accuracy_m=payload.gps_accuracy_m,
        orientation=payload.orientation,
        captured_at=payload.captured_at,
        photo1_url=photo1_url,
        photo2_url=photo2_url,
        photo1_phash=photo1_phash,
        photo2_phash=photo2_phash,
        remarks=payload.remarks,
        observer_id=payload.observer_id,
        observer_name=payload.observer_name,
        organisation=payload.organisation,
        geom=from_shape(Point(payload.lon, payload.lat), srid=4326),
        is_synthetic=payload.is_synthetic,
        photo_source=payload.photo_source,
    )
    db.add(record)
    db.flush()  # assign record.id before creating the dependent asset_evidence row

    geo_flags_json = [
        {"rule": f.rule, "passed": f.passed, "points": f.points, "max": f.max, "detail": f.detail}
        for f in result.geo_flags
    ]
    evidence = AssetEvidence(record_id=record.id, geo_flags=geo_flags_json, geo_score=result.geo_score)
    db.add(evidence)
    db.commit()
    db.refresh(record)

    _ = photo1_filename  # kept for clarity/debugging; url is the source of truth returned to callers

    return RecordIngestOut(
        record=FieldRecordOut.model_validate(record, from_attributes=True),
        geo_integrity=GeoIntegrityOut(
            geo_score=result.geo_score,
            geo_flags=[
                GeoFlagOut(rule=f.rule, passed=f.passed, points=f.points, max=f.max, detail=f.detail)
                for f in result.geo_flags
            ],
        ),
    )
