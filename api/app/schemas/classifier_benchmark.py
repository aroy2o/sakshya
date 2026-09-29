"""GET /classifier/benchmark — Reality Pass R5 (docs/REAL_DATA_PLAN.md §8's R5
row).

Not in PRD.md's original §9 API table (that table predates the Reality
Pass) — added the same way GET /programme/marigaon was for R3: a new
endpoint documented here rather than silently bolted on. Mirrors
scripts/run_real_photo_benchmark.py's summary JSON field-for-field; this
schema is the typed contract between that offline script's output and the
live API's response.

Exposes the classifier's measured accuracy against a real, CC-licensed photo
set — never the AI-generated synthetic set's accuracy (see
app/services/classifier_benchmark.py's module docstring for why that
distinction matters and how it's kept honest here).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ClassifierBenchmarkDataset(BaseModel):
    n_photos: int
    source: str
    categories_covered: list[str]  # subset of PRD §15.1's 9 codes actually represented
    categories_not_covered: list[str]
    includes_none_distractors: bool
    is_synthetic: bool = False
    methodology_doc: str
    manifest_fields: list[str]


class ClassifierBenchmarkModelResult(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )  # confusion_matrix keys vary by which ground-truth codes were seen

    model: str
    provider: str
    n_photos: int
    n_correct: int
    n_errors: int
    accuracy: float
    axis_labels: list[str]
    confusion_matrix: dict[str, dict[str, int]]
    generated_at: str
    note: str


class ClassifierBenchmarkOut(BaseModel):
    dataset: ClassifierBenchmarkDataset
    models: list[ClassifierBenchmarkModelResult]
    note: str
