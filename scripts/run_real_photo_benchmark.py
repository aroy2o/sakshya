#!/usr/bin/env python3
"""
R5 — classify the real-photo benchmark set (scripts/real_photos/manifest.json,
built by fetch_real_benchmark_photos.py) with a local Ollama vision model and
score it against ground truth, producing a confusion matrix + accuracy.

Ground truth here is NOT "does this photo match a declared SAKSHYA activity"
(that's PRD §12.2's matches_declared question, answered against a specific
field_record). These Commons photos have no declared_activity at all — ground
truth is instead, per docs/REAL_DATA_PLAN.md §8's R5 row: "which of the 9 PRD
§15.1 categories (or none) does this photo genuinely depict" (assigned by hand
when the benchmark set was curated, see manifest.json's ground_truth_category).

To read the model's own category call without anchoring it toward one
specific label, every photo is classified with a neutral
declared_category="UNKNOWN" / declared_activity phrase that names no
category — the classifier's build_classifier_prompt() still asks "what
category is this" the same way it does in production, it's just not told
which one to expect. matches_declared/visual_score are recorded but are NOT
the accuracy metric here (they'd only be meaningful against a real declared
activity) — the metric is predicted_category vs. ground_truth_category, with
predicted_category="UNKNOWN" counted correct when ground_truth is "NONE".

CRITICAL (CLAUDE.md / REAL_DATA_PLAN.md §8 R5): this script's output is a
SEPARATE, honestly-labelled metric from scripts/batch_classify.py's runs
against the AI-generated synthetic photo set. Never merge the two or present
one as the other.

Usage:
  python scripts/run_real_photo_benchmark.py --model moondream
  python scripts/run_real_photo_benchmark.py --model llava
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from services.vision_classifier import ActivityCategory, VisionClassifierService  # noqa: E402
from services.vision_providers.ollama_provider import OllamaVisionProvider  # noqa: E402

REAL_PHOTOS_DIR = Path(__file__).resolve().parent / "real_photos"
MANIFEST_PATH = REAL_PHOTOS_DIR / "manifest.json"

# 9 PRD §15.1 codes + ground truth's own "NONE" (distractor rows/cols use the
# classifier's own "UNKNOWN" label so the confusion matrix has one consistent axis)
CATEGORY_CODES = [c.value for c in ActivityCategory if c is not ActivityCategory.UNKNOWN]
AXIS_LABELS = CATEGORY_CODES + ["UNKNOWN"]  # predicted axis; ground truth "NONE" maps to "UNKNOWN" for scoring

NEUTRAL_DECLARED_CATEGORY = "UNKNOWN"
# Kept short and plain on purpose: an early version of this string used
# parenthetical meta-commentary ("real-photo benchmark — no declared label
# provided") and moondream sometimes echoed fragments of it back into
# predicted_category/predicted_activity instead of picking a real enum value
# (e.g. predicted_category="unspecified"). Confirmed by direct comparison
# against a real declared_category+activity on the same image (which produced
# a clean, valid response) that this was prompt wording, not a resource/
# timeout artifact. This shorter phrasing still names no PRD §15.1 category
# (keeps the "don't anchor the answer" property) while giving the model less
# unusual text to get distracted by.
NEUTRAL_DECLARED_ACTIVITY = "a general rural or agricultural scene"


def gt_to_axis(code: str) -> str:
    """Ground truth 'NONE' and the classifier's own 'UNKNOWN' predicted label
    are the same concept on this confusion matrix's axis."""
    return "UNKNOWN" if code == "NONE" else code


def stratified_sample(manifest: list[dict], max_per_category: int) -> list[dict]:
    """Cap the number of photos per ground_truth_category, preserving
    manifest order within each category — used to bound a run's wall-clock
    time/RAM-pressure duration (e.g. a heavier alternative model on a tight
    machine) while still exercising every category, rather than either
    running the full set or skipping the model entirely."""
    counts: dict[str, int] = defaultdict(int)
    sampled = []
    for entry in manifest:
        cat = entry["ground_truth_category"]
        if counts[cat] < max_per_category:
            sampled.append(entry)
            counts[cat] += 1
    return sampled


def run(model: str, out_dir: Path, *, resume: bool = True, max_per_category: int | None = None) -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text())
    if max_per_category is not None:
        manifest = stratified_sample(manifest, max_per_category)
    provider = OllamaVisionProvider(model=model)
    service = VisionClassifierService(provider, max_retries=1)

    results_path = out_dir / f"benchmark_results_{model}.json"

    # Resume support: local CPU/GPU-shared inference on a resource-contended
    # dev machine is slow enough (and this environment interruptible enough —
    # rate limits, other agents competing for RAM/GPU) that re-classifying
    # photos already done on a previous run would waste real time. Skip any
    # id already present in an existing results file for this model unless
    # --no-resume was passed (e.g. after a prompt-wording change, where old
    # entries used a different, no-longer-comparable condition).
    per_photo: list[dict] = []
    already_done: set[str] = set()
    if resume and results_path.exists():
        try:
            per_photo = json.loads(results_path.read_text())
            already_done = {e["id"] for e in per_photo if e.get("predicted_category") is not None or e.get("error")}
        except (json.JSONDecodeError, KeyError):
            per_photo = []
    if already_done:
        print(f"Resuming: {len(already_done)}/{len(manifest)} already classified, skipping those", file=sys.stderr)

    confusion: dict[str, Counter] = defaultdict(Counter)  # confusion[ground_truth_axis][predicted] += 1
    n_correct = 0
    n_errors = 0
    # re-seed counters/confusion from any resumed entries so the summary is complete
    for e in per_photo:
        if e["id"] in already_done:
            if e.get("correct"):
                n_correct += 1
            if e.get("error"):
                n_errors += 1
            if e.get("predicted_category") is not None:
                confusion[gt_to_axis(e["ground_truth_category"])][e["predicted_category"]] += 1

    for i, entry in enumerate(manifest, start=1):
        if entry["id"] in already_done:
            continue
        gt_code = entry["ground_truth_category"]
        gt_axis = gt_to_axis(gt_code)
        local_path = Path(__file__).resolve().parent.parent / entry["local_path"]
        t0 = time.monotonic()
        outcome = None
        try:
            outcome = service.classify(
                image_path=local_path,
                declared_category=NEUTRAL_DECLARED_CATEGORY,
                declared_activity=NEUTRAL_DECLARED_ACTIVITY,
            )
            predicted = outcome.ai_result["predicted_category"]
            confidence = outcome.ai_result["confidence"]
            error = None
        except Exception as exc:  # noqa: BLE001 - a real local model call can fail mid-batch
            predicted = None
            confidence = None
            error = str(exc)
            n_errors += 1
        elapsed = time.monotonic() - t0

        correct = predicted == gt_axis
        if correct:
            n_correct += 1
        if predicted is not None:
            confusion[gt_axis][predicted] += 1

        per_photo.append(
            {
                "id": entry["id"],
                "commons_title": entry["commons_title"],
                "ground_truth_category": gt_code,
                "predicted_category": predicted,
                "confidence": confidence,
                "correct": correct,
                "elapsed_s": round(elapsed, 1),
                "error": error,
                "ai_result": outcome.ai_result if outcome is not None else None,
            }
        )
        status = "OK " if correct else ("ERR" if error else "MISS")
        conf_str = f"{confidence:.2f}" if isinstance(confidence, float) else "-"
        print(
            f"  [{i}/{len(manifest)}] {status} gt={gt_axis:8s} pred={str(predicted):8s} "
            f"conf={conf_str} {elapsed:.1f}s  ({entry['commons_title']})",
            file=sys.stderr,
        )
        # write after every photo -- local CPU inference is slow, don't lose progress on interruption
        results_path.write_text(json.dumps(per_photo, indent=2, ensure_ascii=False))

    n_total = len(manifest)
    accuracy = round(n_correct / n_total, 4) if n_total else 0.0
    # A predicted_category of "UNKNOWN" can mean two very different things:
    # the model genuinely looked and couldn't tell (a real ai_result with
    # some evidence text), or VisionClassifierService's retry-then-degrade
    # path kicked in because the raw response failed Pydantic validation
    # (evidence always starts with the fixed string below in that case). This
    # distinction matters a lot for interpreting the accuracy number honestly
    # -- see docs/CLASSIFIER_BENCHMARK.md.
    n_schema_invalid = sum(
        1
        for e in per_photo
        if e.get("ai_result") and str(e["ai_result"].get("evidence", "")).startswith("Classifier response invalid")
    )

    summary = {
        "model": model,
        "provider": "ollama",
        "n_photos": n_total,
        "n_correct": n_correct,
        "n_errors": n_errors,
        "n_schema_invalid_responses": n_schema_invalid,
        "accuracy": accuracy,
        "is_full_dataset": max_per_category is None,
        "max_per_category": max_per_category,
        "axis_labels": AXIS_LABELS,
        "confusion_matrix": {gt: dict(preds) for gt, preds in confusion.items()},
        "neutral_declared_category": NEUTRAL_DECLARED_CATEGORY,
        "neutral_declared_activity": NEUTRAL_DECLARED_ACTIVITY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Measured on REAL Wikimedia Commons photos (scripts/real_photos/manifest.json), "
            "NOT the AI-generated synthetic set from generate_synthetic_photos.py/batch_classify.py. "
            "Do not present this figure interchangeably with synthetic-set accuracy. "
            f"{n_schema_invalid}/{n_total} responses failed structured-output validation and were "
            "degraded to an honest UNKNOWN/0.0-confidence result rather than a guessed category "
            "(services/vision_classifier.py's designed fallback) -- these are NOT the same as the "
            "model confidently looking and reporting it doesn't know."
        ),
    }
    summary_path = out_dir / f"benchmark_summary_{model}.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n{model}: {n_correct}/{n_total} correct = {accuracy:.1%} accuracy ({n_errors} error(s))", file=sys.stderr)
    print(f"Wrote {results_path} and {summary_path}", file=sys.stderr)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Ollama model tag, e.g. moondream or llava")
    parser.add_argument("--out-dir", type=Path, default=REAL_PHOTOS_DIR)
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="ignore any existing benchmark_results_<model>.json and reclassify every photo from scratch",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=None,
        help=(
            "bound the run to at most N photos per ground_truth_category (stratified sample) instead of "
            "the full 45-photo set -- for a heavier model on limited time/RAM, still exercising every "
            "category rather than skipping the model entirely (see docs/CLASSIFIER_BENCHMARK.md)"
        ),
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    run(args.model, args.out_dir, resume=not args.no_resume, max_per_category=args.max_per_category)


if __name__ == "__main__":
    main()
