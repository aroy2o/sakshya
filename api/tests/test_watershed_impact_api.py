"""Integration tests for GET /mws/{id}/watershed-impact (Reality Pass R6
prerequisite - docs/REAL_DATA_PLAN.md §4/§8's R2 row had no API endpoint
wired to it yet; added so R6's "Impact curve" beat has something real to
fetch). Hermetic against geospatial_fixture, same pattern as
test_thematic_api.py / test_satellite_api.py - never depends on the real
scripts/output/ tree.
"""

from __future__ import annotations


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


_SUMMARY = {
    "mws_id": "4120883730",
    "placeholder": True,
    "source": "synthetic_no_gee_credentials",
    "NDVI": {"effect": 0.028, "ci_low": 0.025, "ci_high": 0.031},
}
_TIMESERIES = {
    "mws_id": "4120883730",
    "placeholder": True,
    "source": "synthetic_no_gee_credentials",
    "treated": {"NDVI": {"2020": 0.5}},
}


def test_returns_summary_and_timeseries(client, geospatial_fixture):
    mws_id = _create_mws(client, "IMPACT_MWS_1")
    geospatial_fixture(mws_id, watershed_did_summary=_SUMMARY, watershed_timeseries=_TIMESERIES)

    resp = client.get(f"/mws/{mws_id}/watershed-impact")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mws_id"] == mws_id
    assert body["summary"]["placeholder"] is True
    assert body["timeseries"]["treated"]["NDVI"]["2020"] == 0.5


def test_unknown_mws_404(client):
    resp = client.get("/mws/does-not-exist/watershed-impact")
    assert resp.status_code == 404


def test_no_precompute_yet_404(client, geospatial_fixture):
    mws_id = _create_mws(client, "IMPACT_MWS_2")
    # deliberately no watershed_did_summary/timeseries kwargs - only the
    # thematic/manifest half of the fixture exists for this mws
    geospatial_fixture(mws_id)

    resp = client.get(f"/mws/{mws_id}/watershed-impact")
    assert resp.status_code == 404


def test_endpoint_module_has_no_network_client_imports():
    """Precompute-first non-negotiable: this endpoint must never make a
    live call - it only reads files geospatial-engineer's offline script
    already wrote."""
    import inspect

    from app.routers import watershed_impact

    src = inspect.getsource(watershed_impact)
    for forbidden in ("import ee", "import requests", "import httpx", "urllib.request", "aiohttp"):
        assert forbidden not in src
