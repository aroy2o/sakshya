"""GET /mws/{id}/assets, GET /assets/{id}, POST /assets/{id}/classify (FR2.2),
POST /assets/{id}/satellite (FR3.4) — PRD §9.

classify/satellite both follow the same shape: find the record + its
asset_evidence row, ingest a result from elsewhere (vision-ai-engineer's
classifier / geospatial-engineer's precomputed satellite results), persist
the JSONB-equivalent blob + its INT sub-score, return the full updated asset
detail. Neither ever calls a live external service from this request path
(precompute-first non-negotiable) - the vision call goes through
MockVisionProvider (no live API key exists yet), and satellite data is read
from geospatial-engineer's already-precomputed output files, never GEE.

Response shapes are unchanged by the Postgres->Mongo storage swap - only how
records/evidence get fetched/joined changed (Mongo has no server-side JOIN
the way SQL does at this simple scale, so a "join" here is: fetch the ids,
then fetch the matching evidence docs, then merge in Python).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import get_db
from app.models.asset_evidence import COLLECTION as ASSET_EVIDENCE_COLLECTION
from app.models.field_record import COLLECTION as FIELD_RECORD_COLLECTION
from app.models.mws import COLLECTION as MWS_COLLECTION
from app.schemas.asset_evidence import AssetDetailOut
from app.schemas.common import AssetFeature, AssetFeatureCollection, AssetFeatureProperties
from app.services import geospatial_output, photo_service
from app.services.vision import get_vision_classifier_service
from services.vision_classifier import VisionClassifierService

router = APIRouter(tags=["assets"])


def _to_asset_detail(record: dict, evidence: dict | None) -> AssetDetailOut:
    evidence = evidence or {}
    return AssetDetailOut(
        id=record["_id"],
        work_code=record.get("work_code"),
        mws_id=record["mws_id"],
        category=record["category"],
        activity=record["activity"],
        status=record.get("status"),
        lat=record["lat"],
        lon=record["lon"],
        gps_accuracy_m=record.get("gps_accuracy_m"),
        orientation=record.get("orientation"),
        captured_at=record.get("captured_at"),
        photo1_url=record.get("photo1_url"),
        photo2_url=record.get("photo2_url"),
        photo1_phash=record.get("photo1_phash"),
        photo2_phash=record.get("photo2_phash"),
        remarks=record.get("remarks"),
        observer_id=record.get("observer_id"),
        observer_name=record.get("observer_name"),
        organisation=record.get("organisation"),
        is_synthetic=record.get("is_synthetic", False),
        photo_source=record.get("photo_source"),
        created_at=record["created_at"],
        geo_flags=evidence.get("geo_flags"),
        geo_score=evidence.get("geo_score"),
        ai_result=evidence.get("ai_result"),
        visual_score=evidence.get("visual_score"),
        sat_result=evidence.get("sat_result"),
        satellite_score=evidence.get("satellite_score"),
        temporal_score=evidence.get("temporal_score"),
        evidence_score=evidence.get("evidence_score"),
        band=evidence.get("band"),
        reviewer_decision=evidence.get("reviewer_decision"),
        reviewed_at=evidence.get("reviewed_at"),
        scored_at=evidence.get("scored_at"),
    )


@router.get("/mws/{mws_id}/assets", response_model=AssetFeatureCollection)
def list_mws_assets(mws_id: str, db: Database = Depends(get_db)) -> AssetFeatureCollection:
    if db[MWS_COLLECTION].find_one({"_id": mws_id}, {"_id": 1}) is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")

    records = list(db[FIELD_RECORD_COLLECTION].find({"mws_id": mws_id}))
    ids = [r["_id"] for r in records]
    evidence_by_id = {
        e["_id"]: e
        for e in db[ASSET_EVIDENCE_COLLECTION].find({"_id": {"$in": ids}}, {"evidence_score": 1, "band": 1})
    }

    features = [
        AssetFeature(
            geometry=record["geom"],
            properties=AssetFeatureProperties(
                id=record["_id"],
                work_code=record.get("work_code"),
                category=record["category"],
                activity=record["activity"],
                status=record.get("status"),
                captured_at=record.get("captured_at"),
                photo1_url=record.get("photo1_url"),
                is_synthetic=record.get("is_synthetic", False),
                evidence_score=evidence_by_id.get(record["_id"], {}).get("evidence_score"),
                band=evidence_by_id.get(record["_id"], {}).get("band"),
            ),
        )
        for record in records
    ]
    return AssetFeatureCollection(features=features)


def _get_record_and_evidence(asset_id: int, db: Database) -> tuple[dict, dict | None]:
    record = db[FIELD_RECORD_COLLECTION].find_one({"_id": asset_id})
    if record is None:
        raise HTTPException(404, f"asset {asset_id} not found")
    evidence = db[ASSET_EVIDENCE_COLLECTION].find_one({"_id": asset_id})
    return record, evidence


@router.get("/assets/{asset_id}", response_model=AssetDetailOut)
def get_asset(asset_id: int, db: Database = Depends(get_db)) -> AssetDetailOut:
    record, evidence = _get_record_and_evidence(asset_id, db)
    return _to_asset_detail(record, evidence)


@router.post("/assets/{asset_id}/classify", response_model=AssetDetailOut)
def classify_asset(
    asset_id: int,
    db: Database = Depends(get_db),
    service: VisionClassifierService = Depends(get_vision_classifier_service),
) -> AssetDetailOut:
    """FR2.2 — run vision-ai-engineer's classifier against this asset's
    photo1, persist ai_result + visual_score. Re-running overwrites the
    previous classification (PRD §9: "Run/re-run").

    `service` is a FastAPI dependency (not a plain function call) specifically
    so tests can override it via `app.dependency_overrides` to get
    deterministic MockVisionProvider behavior regardless of whichever
    provider get_vision_classifier_service() currently defaults to for the
    live app (Ollama as of this sync - a real, non-deterministic, possibly-
    unavailable-in-CI local service that integration tests must not depend
    on to stay fast and reliable)."""
    record, evidence = _get_record_and_evidence(asset_id, db)
    if evidence is None:
        raise HTTPException(500, f"asset {asset_id} has no asset_evidence row (should be created at ingest)")
    if not record.get("photo1_url"):
        raise HTTPException(422, f"asset {asset_id} has no photo1_url to classify")

    local_path = photo_service.resolve_local_path(record["photo1_url"])
    if not local_path.exists():
        raise HTTPException(422, f"photo1 file not found on disk at {local_path}")

    outcome = service.classify(local_path, record["category"], record["activity"])

    db[ASSET_EVIDENCE_COLLECTION].update_one(
        {"_id": asset_id},
        {"$set": {"ai_result": outcome.ai_result, "visual_score": outcome.visual_score}},
    )
    evidence = db[ASSET_EVIDENCE_COLLECTION].find_one({"_id": asset_id})
    return _to_asset_detail(record, evidence)


@router.post("/assets/{asset_id}/satellite", response_model=AssetDetailOut)
def ingest_satellite_result(asset_id: int, db: Database = Depends(get_db)) -> AssetDetailOut:
    """FR3.4 — ingest geospatial-engineer's precomputed per-record satellite
    result (scripts/output/{mws_id}/satellite_results.json) into
    asset_evidence.sat_result + satellite_score. Never calls Earth Engine or
    computes anything here - geospatial-engineer's offline script already did
    the DiD scoring per PRD §12.3; this just persists it."""
    record, evidence = _get_record_and_evidence(asset_id, db)
    if evidence is None:
        raise HTTPException(500, f"asset {asset_id} has no asset_evidence row (should be created at ingest)")

    try:
        results = geospatial_output.load_satellite_results(record["mws_id"])
    except FileNotFoundError:
        raise HTTPException(
            404, f"no precomputed satellite results for mws {record['mws_id']!r} yet"
        ) from None

    match = next((r for r in results if r.get("record_id") == asset_id), None)
    if match is None:
        raise HTTPException(404, f"no precomputed satellite result found for asset {asset_id}")

    satellite_score = match.get("satellite_score")
    if not isinstance(satellite_score, int):
        raise HTTPException(
            500, f"precomputed result for asset {asset_id} is missing a valid integer satellite_score"
        )

    db[ASSET_EVIDENCE_COLLECTION].update_one(
        {"_id": asset_id},
        {"$set": {"sat_result": match, "satellite_score": satellite_score}},
    )
    evidence = db[ASSET_EVIDENCE_COLLECTION].find_one({"_id": asset_id})
    return _to_asset_detail(record, evidence)
