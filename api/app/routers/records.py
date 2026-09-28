"""POST /records — PRD §9 / FR1.3.

Runs the geo-integrity validator synchronously and always ingests the record
regardless of how badly it fails geo-integrity: the whole point of
geo_score/bands/the Phase 6 review queue is to surface suspect records, not
silently drop them. Never calls a live vision/GEE service (precompute-first
non-negotiable) - only geo_score is populated here.

geo_integrity.py itself is untouched by the Postgres->Mongo storage swap
(it's pure/Shapely-based, already DB-independent) - only how its inputs get
fetched changed: the mws boundary is now `shapely.geometry.shape(mws_doc["geom"])`
directly on the stored GeoJSON dict, instead of GeoAlchemy2's `to_shape`.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pymongo.database import Database
from shapely.geometry import Point, mapping, shape

from app.db import get_db
from app.models.asset_evidence import COLLECTION as ASSET_EVIDENCE_COLLECTION
from app.models.field_record import COLLECTION as FIELD_RECORD_COLLECTION
from app.models.mws import COLLECTION as MWS_COLLECTION
from app.schemas.common import GeoFlagOut
from app.schemas.field_record import FieldRecordIn, FieldRecordOut, GeoIntegrityOut, RecordIngestOut
from app.services import geo_integrity, photo_service
from app.services.sequences import next_sequence

router = APIRouter(tags=["records"])


@router.post("/records", response_model=RecordIngestOut, status_code=201)
async def create_record(
    metadata: str = Form(..., description="JSON-encoded field-record metadata (see FieldRecordIn schema)"),
    photo1: UploadFile = File(..., description="Primary evidence photo - required"),
    photo2: UploadFile | None = File(None, description="Secondary photo - optional"),
    db: Database = Depends(get_db),
) -> RecordIngestOut:
    try:
        payload = FieldRecordIn.model_validate_json(metadata)
    except Exception as exc:  # pydantic ValidationError or JSON decode error
        raise HTTPException(422, f"invalid metadata JSON: {exc}") from exc

    mws_doc = db[MWS_COLLECTION].find_one({"_id": payload.mws_id})
    if mws_doc is None:
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

    existing_phashes = [
        d["photo1_phash"]
        for d in db[FIELD_RECORD_COLLECTION].find({"photo1_phash": {"$ne": None}}, {"photo1_phash": 1})
    ] + [
        d["photo2_phash"]
        for d in db[FIELD_RECORD_COLLECTION].find({"photo2_phash": {"$ne": None}}, {"photo2_phash": 1})
    ]

    boundary = shape(mws_doc["geom"])
    window_start = dt.date.fromisoformat(mws_doc["baseline_start"]) if mws_doc.get("baseline_start") else None
    window_end = dt.date.fromisoformat(mws_doc["latest_end"]) if mws_doc.get("latest_end") else None

    geo_input = geo_integrity.GeoIntegrityInput(
        lat=payload.lat,
        lon=payload.lon,
        gps_accuracy_m=payload.gps_accuracy_m,
        captured_at=payload.captured_at,
        boundary=boundary,
        window_start=window_start,
        window_end=window_end,
        now=dt.datetime.now(dt.UTC),
        photo1_exif=photo1_exif,
        photo1_phash=photo1_phash,
        photo2_phash=photo2_phash,
        existing_phashes=existing_phashes,
    )
    result = geo_integrity.evaluate(geo_input)

    record_id = next_sequence(db, "field_record_id")
    created_at = dt.datetime.now(dt.UTC)
    record_doc = {
        "_id": record_id,
        "work_code": payload.work_code,
        "mws_id": payload.mws_id,
        "category": payload.category,
        "activity": payload.activity,
        "status": payload.status,
        "lat": payload.lat,
        "lon": payload.lon,
        "gps_accuracy_m": payload.gps_accuracy_m,
        "orientation": payload.orientation,
        "captured_at": payload.captured_at,
        "photo1_url": photo1_url,
        "photo2_url": photo2_url,
        "photo1_phash": photo1_phash,
        "photo2_phash": photo2_phash,
        "remarks": payload.remarks,
        "observer_id": payload.observer_id,
        "observer_name": payload.observer_name,
        "organisation": payload.organisation,
        "geom": mapping(Point(payload.lon, payload.lat)),
        "is_synthetic": payload.is_synthetic,
        "photo_source": payload.photo_source,
        "created_at": created_at,
    }
    db[FIELD_RECORD_COLLECTION].insert_one(record_doc)

    geo_flags_json = [
        {"rule": f.rule, "passed": f.passed, "points": f.points, "max": f.max, "detail": f.detail}
        for f in result.geo_flags
    ]
    evidence_doc = {
        "_id": record_id,
        "geo_flags": geo_flags_json,
        "geo_score": result.geo_score,
        "ai_result": None,
        "visual_score": None,
        "sat_result": None,
        "satellite_score": None,
        "temporal_score": None,
        "evidence_score": None,
        "band": None,
        "reviewer_decision": None,
        "reviewed_at": None,
        "scored_at": None,
    }
    db[ASSET_EVIDENCE_COLLECTION].insert_one(evidence_doc)

    _ = photo1_filename  # kept for clarity/debugging; url is the source of truth returned to callers

    return RecordIngestOut(
        record=FieldRecordOut(
            id=record_id,
            work_code=record_doc["work_code"],
            mws_id=record_doc["mws_id"],
            category=record_doc["category"],
            activity=record_doc["activity"],
            status=record_doc["status"],
            lat=record_doc["lat"],
            lon=record_doc["lon"],
            gps_accuracy_m=record_doc["gps_accuracy_m"],
            orientation=record_doc["orientation"],
            captured_at=record_doc["captured_at"],
            photo1_url=record_doc["photo1_url"],
            photo2_url=record_doc["photo2_url"],
            photo1_phash=record_doc["photo1_phash"],
            photo2_phash=record_doc["photo2_phash"],
            remarks=record_doc["remarks"],
            observer_id=record_doc["observer_id"],
            observer_name=record_doc["observer_name"],
            organisation=record_doc["organisation"],
            is_synthetic=record_doc["is_synthetic"],
            photo_source=record_doc["photo_source"],
            created_at=created_at,
        ),
        geo_integrity=GeoIntegrityOut(
            geo_score=result.geo_score,
            geo_flags=[
                GeoFlagOut(rule=f.rule, passed=f.passed, points=f.points, max=f.max, detail=f.detail)
                for f in result.geo_flags
            ],
        ),
    )
