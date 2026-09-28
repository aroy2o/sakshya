"""Read-only access to R5's precomputed real-photo classifier benchmark
(scripts/real_photos/, written by scripts/fetch_real_benchmark_photos.py and
scripts/run_real_photo_benchmark.py).

Precompute-first, same pattern as app/services/programme_registry.py and
app/services/geospatial_output.py: this module never calls Wikimedia Commons
or a local Ollama model itself — it only reads manifest.json (the curated,
downloaded photo set + per-file provenance) and whichever
benchmark_summary_<model>.json files those two offline scripts already wrote.
A missing manifest is surfaced as FileNotFoundError, turned into a clear 404
by the router, never silently faked (CLAUDE.md "never fabricate a number").

CRITICAL distinction this module exists to keep visible (docs/REAL_DATA_PLAN.md
§8 R5 row): the accuracy figures here are measured on REAL Wikimedia Commons
photos, never on the AI-generated synthetic set from
scripts/generate_synthetic_photos.py / scripts/batch_classify.py. Nothing in
this module reads that synthetic set's results.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings

PRD_CATEGORY_CODES = ["AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"]


def real_photos_output_dir() -> Path:
    return Path(get_settings().real_photos_output_dir)


def load_manifest() -> list[dict]:
    """Raises FileNotFoundError if fetch_real_benchmark_photos.py hasn't been
    run yet — caller turns that into a 404."""
    path = real_photos_output_dir() / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_model_summaries() -> list[dict]:
    """Every benchmark_summary_<model>.json present (0, 1, or 2+ — however
    many models run_real_photo_benchmark.py has been run against so far).
    Not an error if none exist yet: the photo set can be downloaded and
    documented before a model has finished classifying it."""
    summaries = []
    for path in sorted(real_photos_output_dir().glob("benchmark_summary_*.json")):
        summaries.append(json.loads(path.read_text(encoding="utf-8")))
    return summaries


def build_benchmark_response() -> dict:
    manifest = load_manifest()  # raises FileNotFoundError -> 404 if absent
    ground_truth_codes = {entry["ground_truth_category"] for entry in manifest}
    covered = sorted(c for c in ground_truth_codes if c != "NONE")
    not_covered = sorted(c for c in PRD_CATEGORY_CODES if c not in covered)

    return {
        "dataset": {
            "n_photos": len(manifest),
            "source": "Wikimedia Commons (individually hand-picked CC-licensed files, not a bulk crawl)",
            "categories_covered": covered,
            "categories_not_covered": not_covered,
            "includes_none_distractors": "NONE" in ground_truth_codes,
            "is_synthetic": False,
            "methodology_doc": "docs/CLASSIFIER_BENCHMARK.md",
            "manifest_fields": [
                "id",
                "ground_truth_category",
                "commons_title",
                "file_page_url",
                "author",
                "license_short",
                "license_url",
                "retrieved_at",
            ],
        },
        "models": load_model_summaries(),
        "note": (
            "Accuracy figures here are measured on REAL Wikimedia Commons photos "
            "with hand-assigned ground truth, NOT on the AI-generated synthetic photo "
            "set used elsewhere in this project (scripts/generate_synthetic_photos.py / "
            "scripts/batch_classify.py). The two must never be presented interchangeably."
        ),
    }
