"""Integration tests for GET /districts/geotag-coverage (FR5.5).

No DB involved (static table, per PRD §9) - these still use the `client`
fixture purely for a real FastAPI TestClient/HTTP round trip, not for any
data setup.
"""

from __future__ import annotations


def test_returns_real_data_matching_frontend_schema(client):
    resp = client.get("/districts/geotag-coverage")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 40  # 31 Assam + 12 Meghalaya + 8 Tripura

    for row in body:
        assert set(row.keys()) >= {
            "district",
            "state",
            "total_works",
            "geotagged_works",
            "geotag_coverage_pct",
        }
        assert isinstance(row["district"], str) and row["district"]
        assert isinstance(row["state"], str) and row["state"]
        assert row["total_works"] >= 0
        assert row["geotagged_works"] >= 0
        assert 0.0 <= row["geotag_coverage_pct"] <= 100.0


def test_includes_demo_watershed_district(client):
    """Morigaon is our demo watershed's district (PRD §14) - this is the
    coordinator's explicit priority case."""
    resp = client.get("/districts/geotag-coverage")
    body = resp.json()
    morigaon = next(r for r in body if r["district"] == "Morigaon" and r["state"] == "Assam")
    assert morigaon["total_works"] == 309
    assert morigaon["geotagged_works"] == 267
    assert morigaon["geotag_coverage_pct"] == 86.4


def test_pct_is_consistent_with_raw_counts_and_never_exceeds_100(client):
    resp = client.get("/districts/geotag-coverage")
    for row in resp.json():
        if row["total_works"] == 0:
            continue
        expected = min(round(row["geotagged_works"] / row["total_works"] * 100, 1), 100.0)
        assert row["geotag_coverage_pct"] == expected


def test_covers_multiple_states(client):
    resp = client.get("/districts/geotag-coverage")
    states = {r["state"] for r in resp.json()}
    assert states == {"Assam", "Meghalaya", "Tripura"}


def test_endpoint_module_has_no_network_client_imports():
    """PRD §9: 'not live-scraped during demo' - a static table means zero
    HTTP-client machinery in the request path, not just "happens to work
    offline today". Checked at the source level rather than by blocking
    sockets at runtime, since TestClient's in-process ASGI transport doesn't
    touch real sockets anyway (that would make a socket-block assertion
    pass trivially without proving anything)."""
    import inspect

    from app.routers import districts
    from app.services import district_coverage

    src = inspect.getsource(districts) + inspect.getsource(district_coverage)
    for forbidden in ("import requests", "import httpx", "urllib.request", "aiohttp"):
        assert forbidden not in src
