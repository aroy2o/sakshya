"""Integration tests for GET /programme/marigaon (Reality Pass R3,
docs/REAL_DATA_PLAN.md §8's R3 row).

Uses the `programme_fixture` fixture (api/tests/conftest.py) to write a
small fake scripts/output/registry/programme_marigaon.json under an
isolated test dir - never touches (or depends on) the real R3 output from
scripts/fetch_gt2.py, same isolation pattern as thematic/satellite tests
use for geospatial-engineer's output.
"""

from __future__ import annotations


def test_returns_404_when_registry_not_yet_precomputed(client):
    """Before scripts/fetch_gt2.py has ever run, this must be a clean 404,
    never a fabricated/default response (CLAUDE.md "never fabricate a
    number")."""
    resp = client.get("/programme/marigaon")
    assert resp.status_code == 404


def test_returns_precomputed_registry_data(client, programme_fixture):
    programme_fixture()
    resp = client.get("/programme/marigaon")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["district"] == "Morigaon"
    assert body["state"] == "Assam"
    assert body["is_synthetic"] is False

    # Cross-check point explicitly called out in the task: these numbers
    # must match GET /districts/geotag-coverage's Morigaon row exactly.
    assert body["district_total_work_codes"] == 309
    assert body["district_geotagged_work_codes"] == 267
    assert body["district_non_geotagged_work_codes"] == 42

    assert body["focus_project"]["project_name"] == "MARIGAON-WDC - 1 /2021-22"
    assert body["focus_project"]["total_work_codes"] == 263
    assert body["focus_project"]["geotagged_work_codes"] == 240

    assert len(body["projects"]) == 2

    assert body["moderation_backlog_denominator"] == 240
    pre = body["moderation_backlog"]["pre"]
    assert pre["yet_to_moderate"] == 123
    assert pre["yet_to_moderate_pct_of_geotagged"] == 51.2
    # every stage's buckets must sum to the same denominator - this is the
    # "exact, not estimated" backlog figure the task asked for
    for stage in ("pre", "mid", "post"):
        s = body["moderation_backlog"][stage]
        total = (
            s["accepted"]
            + s["yet_to_moderate"]
            + s["rejected"]
            + s["not_submitted"]
            + s["mixed"]
            + s["other"]
        )
        assert total == body["moderation_backlog_denominator"]


def test_category_breakdown_only_uses_the_fixed_9_prd_codes(client, programme_fixture):
    programme_fixture()
    resp = client.get("/programme/marigaon")
    body = resp.json()
    valid = {"AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"}
    for row in body["category_breakdown"]:
        assert row["category"] in valid


def test_endpoint_module_has_no_network_client_imports():
    """Precompute-first non-negotiable: this endpoint must be a static file
    read only, never a live call to wdcpmksy.dolr.gov.in from the request
    path."""
    import inspect

    from app.routers import programme
    from app.services import programme_registry

    src = inspect.getsource(programme) + inspect.getsource(programme_registry)
    for forbidden in ("import requests", "import httpx", "urllib.request", "aiohttp"):
        assert forbidden not in src
