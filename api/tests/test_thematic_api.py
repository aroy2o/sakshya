"""Integration tests for GET /mws/{id}/thematic/{layer} (FR3.3 wiring)."""

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


def test_raster_layer_returns_tile_url_and_bounds(client, geospatial_fixture):
    mws_id = _create_mws(client, "THEMATIC_MWS_1")
    geospatial_fixture(mws_id)

    resp = client.get(f"/mws/{mws_id}/thematic/ndvi_before")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["layer"] == "ndvi_before"
    assert body["kind"] == "raster"
    assert body["bounds"] == [92.28, 26.18, 92.30, 26.20]
    assert body["tile_url"].endswith(f"/{mws_id}/thematic/ndvi_before.png")
    assert body["geojson"] is None
    assert body["placeholder"] is True
    assert len(body["legend"]) > 0

    # the URL should actually be servable
    img_resp = client.get(body["tile_url"].replace("http://testserver", ""))
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/png"


def test_vector_layer_returns_geojson_and_falls_back_to_mws_bounds(client, geospatial_fixture):
    mws_id = "THEMATIC_MWS_2"
    payload = {
        "id": mws_id,
        "boundary": {
            "type": "Polygon",
            "coordinates": [[[91.95, 25.95], [92.05, 25.95], [92.05, 26.05], [91.95, 26.05], [91.95, 25.95]]],
        },
        "is_synthetic_boundary": True,
    }
    assert client.post("/mws", json=payload).status_code == 201
    geospatial_fixture(mws_id)

    resp = client.get(f"/mws/{mws_id}/thematic/drainage")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kind"] == "vector"
    assert body["geojson"]["type"] == "FeatureCollection"
    assert body["tile_url"] is None
    # drainage has no "bounds" in the manifest fixture -> falls back to the
    # mws polygon's own bbox (91.95, 25.95, 92.05, 26.05)
    assert body["bounds"] == [91.95, 25.95, 92.05, 26.05]


def test_unknown_layer_404(client, geospatial_fixture):
    mws_id = _create_mws(client, "THEMATIC_MWS_3")
    geospatial_fixture(mws_id)
    resp = client.get(f"/mws/{mws_id}/thematic/slope")  # supporting_artifacts, not exposed here
    assert resp.status_code == 404


def test_layer_not_in_manifest_404(client, geospatial_fixture):
    mws_id = _create_mws(client, "THEMATIC_MWS_4")
    geospatial_fixture(mws_id)  # fixture only populates ndvi_before + drainage
    resp = client.get(f"/mws/{mws_id}/thematic/water")
    assert resp.status_code == 404


def test_unknown_mws_404(client):
    resp = client.get("/mws/NO_SUCH_MWS/thematic/ndvi_before")
    assert resp.status_code == 404


def test_no_precompute_yet_404(client):
    mws_id = _create_mws(client, "THEMATIC_MWS_5")
    # deliberately no geospatial_fixture() call - no precompute exists for this mws
    resp = client.get(f"/mws/{mws_id}/thematic/ndvi_before")
    assert resp.status_code == 404
