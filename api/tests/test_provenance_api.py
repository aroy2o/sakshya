"""Integration tests for GET /provenance (Reality Pass R4,
docs/REAL_DATA_PLAN.md §3 rule 2, §8's R4 row).

No DB/file fixture needed - entries are an in-process Python list
(app/services/provenance_sources), same reasoning as
test_districts_api.py's "no live network call" test below.
"""

from __future__ import annotations


def test_returns_at_least_the_known_backend_datasets(client):
    resp = client.get("/provenance")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    names = {row["name"] for row in body}
    assert any("GT2" in n and "geotag coverage" in n for n in names)
    assert any("GT2" in n and "Marigaon work-code registry" in n for n in names)
    assert any("Synthetic" in n and "seed" in n for n in names)


def test_every_entry_is_typed_and_synthetic_flag_is_never_missing(client):
    resp = client.get("/provenance")
    for row in resp.json():
        assert set(row.keys()) >= {
            "name",
            "licence",
            "is_synthetic",
            "used_for",
            "owner",
        }
        assert isinstance(row["is_synthetic"], bool)
        assert row["name"]
        assert row["licence"]
        assert row["used_for"]
        assert row["owner"]


def test_real_entries_carry_a_source_url_and_retrieved_at(client):
    """CLAUDE.md 'never fabricate a number': a real (non-synthetic) dataset
    must be traceable to where it came from and when."""
    resp = client.get("/provenance")
    for row in resp.json():
        if not row["is_synthetic"]:
            assert row["source_url"], f"real entry {row['name']!r} has no source_url"
            assert row["retrieved_at"], f"real entry {row['name']!r} has no retrieved_at"


def test_synthetic_seed_records_entry_carries_photo_source(client):
    """CLAUDE.md non-negotiable: whenever is_synthetic=true for a
    photo-bearing dataset, photo_source must be set too."""
    resp = client.get("/provenance")
    seed_entry = next(r for r in resp.json() if "Synthetic" in r["name"] and "seed" in r["name"])
    assert seed_entry["is_synthetic"] is True
    assert seed_entry["photo_source"] == "ai_generated"


def test_marigaon_registry_entry_matches_programme_endpoint_source():
    """The provenance entry's source_url should be the same GT2 work-code
    detail endpoint GET /programme/marigaon's data actually came from -
    checked at the source level against scripts/fetch_gt2.py's own
    constants, not duplicated as a second hardcoded URL that could drift."""
    from app.services.provenance_sources.backend import ENTRIES

    registry_entry = next(e for e in ENTRIES if "work-code registry" in e.name)
    assert "getProjDtlAssetGeoData" in registry_entry.source_url
    assert "projid=90" in registry_entry.source_url


def test_endpoint_module_has_no_network_client_imports():
    """Precompute-first non-negotiable: GET /provenance must never make a
    live call anywhere - it's a literal Python list."""
    import inspect

    from app.routers import provenance
    from app.services import provenance_sources

    src = inspect.getsource(provenance) + inspect.getsource(provenance_sources)
    for forbidden in ("import requests", "import httpx", "urllib.request", "aiohttp"):
        assert forbidden not in src
