"""Integration tests for POST /assets/{id}/classify (FR2.2 wiring)."""

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
        "baseline_start": "2023-01-01",
        "baseline_end": "2023-03-31",
        "latest_start": "2025-01-01",
        "latest_end": "2025-03-31",
        "is_synthetic_boundary": True,
    }
    resp = client.post("/mws", json=payload)
    assert resp.status_code == 201, resp.text
    return mws_id


def _create_record(client, mws_id: str, **overrides) -> dict:
    metadata = dict(
        work_code="WC-001",
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
    metadata.update(overrides)
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = client.post(
        "/records",
        data={"metadata": json.dumps(metadata)},
        files={"photo1": ("photo1.jpg", photo_bytes, "image/jpeg")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["record"]


def test_classify_populates_ai_result_and_visual_score(client):
    mws_id = _create_mws(client, "CLASSIFY_MWS_1")
    record = _create_record(client, mws_id, category="PT", activity="Farm Pond")

    resp = client.post(f"/assets/{record['id']}/classify")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["ai_result"] is not None
    assert body["ai_result"]["matches_declared"] == "yes"
    assert body["ai_result"]["predicted_category"] == "PT"
    assert body["ai_result"]["provider"] == "mock"
    assert body["ai_result"]["needs_review"] is False
    assert isinstance(body["ai_result"]["flags"], list)
    assert body["visual_score"] == 30  # matches_declared=yes, confidence>=0.75 -> PRD §12.2 full marks

    # geo_score from ingest must be untouched by classify
    assert body["geo_score"] == 30
    # Phase 3/4 fields still null - classify only ever touches ai_result/visual_score
    assert body["sat_result"] is None
    assert body["satellite_score"] is None
    assert body["evidence_score"] is None
    assert body["band"] is None


def test_classify_is_rerunnable(client):
    mws_id = _create_mws(client, "CLASSIFY_MWS_2")
    record = _create_record(client, mws_id)

    first = client.post(f"/assets/{record['id']}/classify")
    second = client.post(f"/assets/{record['id']}/classify")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["ai_result"]["classified_at"] >= first.json()["ai_result"]["classified_at"]


def test_classify_missing_asset_404(client):
    resp = client.post("/assets/999999/classify")
    assert resp.status_code == 404


def test_classify_via_full_asset_detail_roundtrip(client):
    """GET /assets/{id} after classify should reflect the persisted result -
    same DB row, two different endpoints."""
    mws_id = _create_mws(client, "CLASSIFY_MWS_3")
    record = _create_record(client, mws_id)

    client.post(f"/assets/{record['id']}/classify")
    detail = client.get(f"/assets/{record['id']}")
    assert detail.status_code == 200
    assert detail.json()["visual_score"] == 30
    assert detail.json()["ai_result"]["needs_review"] is False
