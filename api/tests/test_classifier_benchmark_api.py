"""Integration tests for GET /classifier/benchmark (Reality Pass R5,
docs/REAL_DATA_PLAN.md §8's R5 row).

Uses the `real_photos_fixture` fixture (api/tests/conftest.py) to write a
small fake scripts/real_photos/manifest.json + benchmark_summary_*.json under
an isolated test dir - never touches (or depends on) the real R5 output from
scripts/fetch_real_benchmark_photos.py / scripts/run_real_photo_benchmark.py,
same isolation pattern test_programme_api.py uses for R3's output.
"""

from __future__ import annotations


def test_returns_404_when_benchmark_not_yet_precomputed(client):
    """Before scripts/fetch_real_benchmark_photos.py has ever run, this must
    be a clean 404, never a fabricated/default response (CLAUDE.md "never
    fabricate a number")."""
    resp = client.get("/classifier/benchmark")
    assert resp.status_code == 404


def test_returns_dataset_info_even_before_any_model_has_run(client, real_photos_fixture):
    """The photo set + provenance can exist before a model has finished
    classifying it - models should just be an empty list, not a 404."""
    real_photos_fixture(with_model_summary=False)
    resp = client.get("/classifier/benchmark")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dataset"]["n_photos"] == 2
    assert body["dataset"]["is_synthetic"] is False
    assert body["models"] == []


def test_returns_precomputed_benchmark_data(client, real_photos_fixture):
    real_photos_fixture()
    resp = client.get("/classifier/benchmark")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["dataset"]["n_photos"] == 2
    assert body["dataset"]["categories_covered"] == ["SM"]
    assert "OM" in body["dataset"]["categories_not_covered"]
    assert body["dataset"]["includes_none_distractors"] is True
    assert body["dataset"]["is_synthetic"] is False

    assert len(body["models"]) == 1
    model = body["models"][0]
    assert model["model"] == "moondream"
    assert model["provider"] == "ollama"
    assert model["n_photos"] == 2
    assert model["accuracy"] == 0.5
    assert model["confusion_matrix"]["SM"]["SM"] == 1

    # CLAUDE.md / REAL_DATA_PLAN.md §8 R5: this must never be silently
    # conflated with the AI-generated synthetic photo set's accuracy.
    assert "synthetic" in body["note"].lower()
    assert "real" in body["note"].lower()


def test_endpoint_module_has_no_network_or_ollama_client_imports():
    """Precompute-first non-negotiable: this endpoint must be a static file
    read only, never a live call to Wikimedia Commons or a local Ollama
    server from the request path."""
    import inspect

    from app.routers import classifier_benchmark
    from app.services import classifier_benchmark as classifier_benchmark_service

    src = inspect.getsource(classifier_benchmark) + inspect.getsource(classifier_benchmark_service)
    for forbidden in ("import requests", "import httpx", "urllib.request", "aiohttp", "ollama"):
        assert forbidden not in src
