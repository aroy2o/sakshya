#!/usr/bin/env python3
"""
FR2.4 — Batch-classify script for the seeded dataset.

Two modes:
  --manifest PATH   Read a photo manifest produced by generate_synthetic_photos.py
                     (or backend-engineer's seed script, once its shape is agreed
                     at Sync Point 1) and classify every record in it. Runs fully
                     offline today against MockVisionProvider; swap --provider
                     once PRD §14's vision-LLM choice + an API key are available.
  --db              Read field_record rows lacking asset_evidence.ai_result from
                     Postgres (DATABASE_URL) and write back ai_result/visual_score.
                     STUBBED — requires backend-engineer's Phase 1 schema/DB to be
                     live; not runnable in this session (no DATABASE_URL set).

Never calls a live vision API from a request path — this is an offline batch job,
consistent with CLAUDE.md's precompute-first rule (applies to the vision-API kind
of "live call" too, not just Earth Engine).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from services.vision_classifier import VisionClassifierService  # noqa: E402
from services.vision_providers.mock import MockVisionProvider  # noqa: E402

DEFAULT_OUT_PATH = Path("scripts/generated_photos/classification_results.json")


def run_manifest_mode(manifest_path: Path, out_path: Path, provider_name: str) -> list[dict]:
    if provider_name != "mock":
        raise SystemExit(
            f"Provider '{provider_name}' requires a live vision API key, which is not configured "
            "in this environment (checked VISION_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY / "
            "GOOGLE_API_KEY — none set). This is a hard stop, not a silent fallback: use "
            "--provider mock, or set a key and wire up a real VisionProvider first."
        )

    records = json.loads(manifest_path.read_text())
    provider = MockVisionProvider()
    service = VisionClassifierService(provider)

    results = []
    for rec in records:
        outcome = service.classify(
            image_path=Path(rec["local_path"]),
            declared_category=rec["declared_category"],
            declared_activity=rec["declared_activity"],
            ground_truth_category=rec.get("ground_truth_category"),
            is_mismatch=rec.get("is_mismatch_test", False),
        )
        results.append(
            {
                "record_id": rec["id"],
                "declared_category": rec["declared_category"],
                "declared_activity": rec["declared_activity"],
                "is_mismatch_test": rec.get("is_mismatch_test", False),
                "ai_result": outcome.ai_result,
                "visual_score": outcome.visual_score,
            }
        )
        gate = "REVIEW-GATED" if outcome.ai_result["needs_review"] else "ok"
        print(
            f"  [{rec['id']}] matches={outcome.ai_result['matches_declared']:<9} "
            f"conf={outcome.ai_result['confidence']:.2f}  visual_score={outcome.visual_score:>2}/30  ({gate})",
            file=sys.stderr,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {len(results)} classification result(s) to {out_path}", file=sys.stderr)
    return results


def run_db_mode(database_url: str | None) -> None:
    database_url = database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "DB mode requires DATABASE_URL (backend-engineer's Phase 1 deliverable). "
            "Not set in this environment — this is a documented blocker, not a silent no-op. "
            "Use --manifest mode instead until the schema/DB is live."
        )
    # STUB: once field_record / asset_evidence exist (PRD §8), this should:
    #   1. SELECT fr.id, fr.category, fr.activity, fr.photo1_url
    #      FROM field_record fr JOIN asset_evidence ae ON ae.record_id = fr.id
    #      WHERE ae.ai_result IS NULL
    #   2. classify each photo1_url via VisionClassifierService
    #   3. UPDATE asset_evidence SET ai_result = :ai_result, visual_score = :visual_score
    #      WHERE record_id = :id
    # Left unimplemented deliberately -- implementing it now would mean guessing
    # backend-engineer's SQLAlchemy session/engine setup, which doesn't exist yet.
    raise NotImplementedError(
        "DB mode is scaffolded but not implemented — needs backend-engineer's SQLAlchemy "
        "models/engine (Phase 1) to exist first. See this function's comment for the intended "
        "query/update shape once that's available."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--manifest", type=Path, help="path to a photo manifest JSON")
    mode.add_argument("--db", action="store_true", help="classify from the live DB (requires DATABASE_URL)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_PATH)
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock"],
        help="only 'mock' is usable without a vision API key (none configured in this environment)",
    )
    args = parser.parse_args()

    if args.db:
        run_db_mode(None)
    else:
        run_manifest_mode(args.manifest, args.out, provider_name=args.provider)


if __name__ == "__main__":
    main()
