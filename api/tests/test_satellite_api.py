"""Integration tests for POST /assets/{id}/satellite (FR3.4 wiring)."""

from __future__ import annotations

import datetime as dt
import json

from tests.factories import make_jpeg_bytes

MWS_LAT, MWS_LON = 26.00, 92.00


def _create_mws(client, mws_id: str) -> str:
    payload = {
        "id": mws_id,
        "boundary": {
            "type": "Polygon",
            "coordinates": [[[91.95, 25.95], [92.05, 25.95], [92.05, 26.05], [91.95, 26.05], [91.95, 25.95]]],
        },
        "is_synthetic_boundary": True,
    }
    resp = client.post("/mws", json=payload)
    assert resp.status_code == 201, resp.text
    return mws_id


def _create_record(client, mws_id: str) -> dict:
    metadata = dict(
        work_code="WC-SAT-001",
        mws_id=mws_id,
        category="PT",
        activity="Farm Pond",
        status="completed",
        lat=MWS_LAT,
        lon=MWS_LON,
        gps_accuracy_m=5.0,
        orientation=0.0,
        captured_at="2025-02-01T09:00:00Z",
        remarks="test",
        observer_id="OBS1",
        observer_name="Test Observer",
        organisation="Test Org",
        is_synthetic=True,
        photo_source="ai_generated",
    )
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = client.post(
        "/records",
        data={"metadata": json.dumps(metadata)},
        files={"photo1": ("photo1.jpg", photo_bytes, "image/jpeg")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["record"]


def test_satellite_ingestion_persists_sat_result_and_score(client, geospatial_fixture):
    mws_id = _create_mws(client, "SAT_MWS_1")
    record = _create_record(client, mws_id)
    record_id = record["id"]

    precomputed = {
        "record_id": record_id,
        "mws_id": mws_id,
        "category": "PT",
        "did": {"NDVI": 0.08, "MNDWI": 0.02},
        "did_classification": "weakly_positive",
        "satellite_score": 18,
        "placeholder": True,
        "source": "synthetic_no_gee_credentials",
    }
    geospatial_fixture(mws_id, satellite_results=[precomputed])

    resp = client.post(f"/assets/{record_id}/satellite")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["satellite_score"] == 18
    assert body["sat_result"]["did_classification"] == "weakly_positive"
    assert body["sat_result"]["record_id"] == record_id
    # geo_score untouched, visual_score/evidence_score still untouched
    assert body["geo_score"] == 30
    assert body["visual_score"] is None
    assert body["evidence_score"] is None


def test_satellite_no_precompute_for_mws_404(client):
    mws_id = _create_mws(client, "SAT_MWS_2")
    record = _create_record(client, mws_id)
    resp = client.post(f"/assets/{record['id']}/satellite")
    assert resp.status_code == 404


def test_satellite_record_not_in_results_404(client, geospatial_fixture):
    mws_id = _create_mws(client, "SAT_MWS_3")
    record = _create_record(client, mws_id)
    geospatial_fixture(mws_id, satellite_results=[{"record_id": record["id"] + 999, "satellite_score": 10}])
    resp = client.post(f"/assets/{record['id']}/satellite")
    assert resp.status_code == 404


def test_satellite_missing_asset_404(client):
    resp = client.post("/assets/999999/satellite")
    assert resp.status_code == 404
