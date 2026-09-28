"""GET /classifier/benchmark — Reality Pass R5 (docs/REAL_DATA_PLAN.md §8's
R5 row).

Serves scripts/fetch_real_benchmark_photos.py's curated real-photo set
provenance and scripts/run_real_photo_benchmark.py's measured
accuracy/confusion-matrix per model tested. Static file read only, same
pattern and same non-negotiable as GET /programme/marigaon: never fetches
Wikimedia Commons or calls Ollama live from a request path
(CLAUDE.md precompute-first).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.classifier_benchmark import ClassifierBenchmarkOut
from app.services import classifier_benchmark

router = APIRouter(tags=["classifier"])


@router.get("/classifier/benchmark", response_model=ClassifierBenchmarkOut)
def get_classifier_benchmark() -> ClassifierBenchmarkOut:
    try:
        data = classifier_benchmark.build_benchmark_response()
    except FileNotFoundError:
        raise HTTPException(
            404,
            "no precomputed real-photo benchmark yet - run scripts/fetch_real_benchmark_photos.py "
            "then scripts/run_real_photo_benchmark.py first",
        ) from None
    return ClassifierBenchmarkOut(**data)
