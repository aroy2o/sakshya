"""Integration tests for POST /records, GET /mws/{id}/assets, GET /assets/{id}."""

from __future__ import annotations

import datetime as dt
import json

from tests.factories import make_jpeg_bytes

MWS_LAT, MWS_LON = 26.00, 92.00


def _boundary_geojson() -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[91.95, 25.95], [92.05, 25.95], [92.05, 26.05], [91.95, 26.05], [91.95, 25.95]]],
    }


def _create_mws(client, mws_id: str) -> str:
    payload = {
        "id": mws_id,
        "boundary": _boundary_geojson(),
        "baseline_start": "2023-01-01",
        "baseline_end": "2023-03-31",
        "latest_start": "2025-01-01",
        "latest_end": "2025-03-31",
        "is_synthetic_boundary": True,
    }
    resp = client.post("/mws", json=payload)
    assert resp.status_code == 201, resp.text
    return mws_id


def _metadata(mws_id: str, **overrides) -> dict:
    base = dict(
        work_code="WC-001",
        mws_id=mws_id,
        category="PT",
        activity="Farm Pond",
        status="completed",
        lat=MWS_LAT,
        lon=MWS_LON,
        gps_accuracy_m=5.0,
        orientation=90.0,
        captured_at="2025-02-01T09:00:00Z",
        remarks="test record",
        observer_id="OBS1",
        observer_name="Test Observer",
        organisation="Test Org",
        is_synthetic=True,
        photo_source="ai_generated",
    )
    base.update(overrides)
    return base


def _post_record(client, mws_id: str, photo_bytes: bytes, **meta_overrides):
    return client.post(
        "/records",
        data={"metadata": json.dumps(_metadata(mws_id, **meta_overrides))},
        files={"photo1": ("photo1.jpg", photo_bytes, "image/jpeg")},
    )


def test_post_records_happy_path(client):
    mws_id = _create_mws(client, "RECORDS_MWS_1")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))

    resp = _post_record(client, mws_id, photo_bytes)
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["geo_integrity"]["geo_score"] == 30
    rules = {f["rule"] for f in body["geo_integrity"]["geo_flags"]}
    assert rules == {
        "gps_accuracy",
        "inside_boundary",
        "exif_consistency",
        "duplicate_photo",
        "timestamp_sane",
    }
    for f in body["geo_integrity"]["geo_flags"]:
        assert set(f.keys()) == {"rule", "passed", "points", "max", "detail"}

    assert body["record"]["is_synthetic"] is True
    assert body["record"]["photo_source"] == "ai_generated"
    assert body["record"]["photo1_url"].startswith("http://testserver/static/photos/")

    asset_id = body["record"]["id"]
    detail = client.get(f"/assets/{asset_id}")
    assert detail.status_code == 200
    d = detail.json()
    assert d["geo_score"] == 30
    # Phase 2/3/4 fields must stay null - never faked
    assert d["ai_result"] is None
    assert d["visual_score"] is None
    assert d["sat_result"] is None
    assert d["satellite_score"] is None
    assert d["temporal_score"] is None
    assert d["evidence_score"] is None
    assert d["band"] is None
    assert d["scored_at"] is None


def test_missing_mws_returns_404(client):
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = _post_record(client, "NO_SUCH_MWS", photo_bytes)
    assert resp.status_code == 404


def test_is_synthetic_requires_photo_source(client):
    mws_id = _create_mws(client, "RECORDS_MWS_2")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = _post_record(client, mws_id, photo_bytes, is_synthetic=True, photo_source=None)
    assert resp.status_code == 422


def test_invalid_category_rejected(client):
    mws_id = _create_mws(client, "RECORDS_MWS_2B")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = _post_record(client, mws_id, photo_bytes, category="ZZ")
    assert resp.status_code == 422


def test_out_of_boundary_ingested_not_rejected(client):
    mws_id = _create_mws(client, "RECORDS_MWS_3")
    bad_lat, bad_lon = 30.0, 95.0
    photo_bytes = make_jpeg_bytes(lat=bad_lat, lon=bad_lon, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = _post_record(client, mws_id, photo_bytes, lat=bad_lat, lon=bad_lon)
    assert resp.status_code == 201  # ingested, never rejected for geo-integrity failure
    flag = next(f for f in resp.json()["geo_integrity"]["geo_flags"] if f["rule"] == "inside_boundary")
    assert flag["passed"] is False
    assert flag["points"] == 0


def test_bad_gps_accuracy_scored_not_rejected(client):
    mws_id = _create_mws(client, "RECORDS_MWS_5")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    resp = _post_record(client, mws_id, photo_bytes, gps_accuracy_m=40.0)
    assert resp.status_code == 201
    flag = next(f for f in resp.json()["geo_integrity"]["geo_flags"] if f["rule"] == "gps_accuracy")
    assert flag["points"] == 0


def test_duplicate_photo_detected_on_second_record(client):
    mws_id = _create_mws(client, "RECORDS_MWS_6")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))

    r1 = _post_record(client, mws_id, photo_bytes, work_code="WC-DUP-1")
    assert r1.status_code == 201
    flag1 = next(f for f in r1.json()["geo_integrity"]["geo_flags"] if f["rule"] == "duplicate_photo")
    assert flag1["passed"] is True

    r2 = _post_record(client, mws_id, photo_bytes, work_code="WC-DUP-2")
    assert r2.status_code == 201
    flag2 = next(f for f in r2.json()["geo_integrity"]["geo_flags"] if f["rule"] == "duplicate_photo")
    assert flag2["passed"] is False
    assert flag2["points"] == 0


def test_missing_exif_scored_not_rejected(client):
    mws_id = _create_mws(client, "RECORDS_MWS_7")
    photo_bytes = make_jpeg_bytes(include_exif=False)
    resp = _post_record(client, mws_id, photo_bytes)
    assert resp.status_code == 201
    flag = next(f for f in resp.json()["geo_integrity"]["geo_flags"] if f["rule"] == "exif_consistency")
    assert flag["points"] == 0


def test_mws_assets_geojson(client):
    mws_id = _create_mws(client, "RECORDS_MWS_4")
    photo_bytes = make_jpeg_bytes(lat=MWS_LAT, lon=MWS_LON, captured_at=dt.datetime(2025, 2, 1, 9, 0, 0))
    assert _post_record(client, mws_id, photo_bytes).status_code == 201

    resp = client.get(f"/mws/{mws_id}/assets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    feature = body["features"][0]
    assert feature["geometry"]["type"] == "Point"
    props = feature["properties"]
    assert props["band"] is None
    assert props["evidence_score"] is None
    assert props["is_synthetic"] is True


def test_asset_not_found(client):
    resp = client.get("/assets/999999")
    assert resp.status_code == 404


def test_mws_assets_unknown_mws_404(client):
    resp = client.get("/mws/NO_SUCH_MWS/assets")
    assert resp.status_code == 404
