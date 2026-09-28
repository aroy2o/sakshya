"""Integration tests for GET /health, POST /mws, GET /mws, GET /mws/{id}.

Requires the docker-compose Postgres+PostGIS test DB (see conftest.py's
`client` fixture) - these tests are skipped implicitly if that DB is
unreachable (the `_migrated_db` fixture's alembic subprocess will raise,
failing the test with a clear connection error rather than silently passing).
"""

from __future__ import annotations


def _boundary_geojson() -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[91.95, 25.95], [92.05, 25.95], [92.05, 26.05], [91.95, 26.05], [91.95, 25.95]]],
    }


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_list_get_mws(client):
    payload = {
        "id": "TEST_MWS_1",
        "name": "Test Watershed",
        "project_id": "SAKSHYA-DEMO",
        "state": "Assam",
        "district": "Morigaon",
        "boundary": _boundary_geojson(),
        "baseline_start": "2023-01-01",
        "baseline_end": "2023-03-31",
        "latest_start": "2025-01-01",
        "latest_end": "2025-03-31",
        "is_synthetic_boundary": True,
    }
    resp = client.post("/mws", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"] == "TEST_MWS_1"
    assert body["boundary"]["type"] == "MultiPolygon"  # Polygon input coerced to MultiPolygon
    assert body["stats"] == {"total_assets": 0, "verified": 0, "review": 0, "flag": 0, "unscored": 0}

    resp = client.get("/mws")
    assert resp.status_code == 200
    assert "TEST_MWS_1" in [m["id"] for m in resp.json()]
    assert "boundary" not in resp.json()[0]  # list view omits geometry by design

    resp = client.get("/mws/TEST_MWS_1")
    assert resp.status_code == 200
    assert resp.json()["district"] == "Morigaon"

    resp = client.get("/mws/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_create_mws_duplicate_id_conflicts(client):
    payload = {"id": "TEST_MWS_DUP", "boundary": _boundary_geojson()}
    assert client.post("/mws", json=payload).status_code == 201
    assert client.post("/mws", json=payload).status_code == 409


def test_create_mws_accepts_multipolygon_directly(client):
    payload = {
        "id": "TEST_MWS_MP",
        "boundary": {"type": "MultiPolygon", "coordinates": [_boundary_geojson()["coordinates"]]},
    }
    resp = client.post("/mws", json=payload)
    assert resp.status_code == 201, resp.text
    assert resp.json()["boundary"]["type"] == "MultiPolygon"
