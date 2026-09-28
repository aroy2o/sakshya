#!/usr/bin/env python3
"""
FR2.4 — Batch-classify script for the seeded dataset.

Two modes:
  --manifest PATH   Read a photo manifest produced by generate_synthetic_photos.py
                     (or backend-engineer's seed script, once its shape is agreed
                     at Sync Point 1) and classify every record in it. Defaults to
                     MockVisionProvider (fast, deterministic); pass --provider ollama
                     to run real local classification via Ollama (see
                     services/vision_providers/ollama_provider.py) — requires
                     `ollama serve` running and the model already pulled
                     (`ollama pull moondream` by default, or set OLLAMA_MODEL).
  --db              Read field_record rows lacking asset_evidence.ai_result from
                     Postgres (DATABASE_URL) and write back ai_result/visual_score.
                     STUBBED — requires backend-engineer's Phase 1 schema/DB to be
                     live; not runnable in this session (no DATABASE_URL set).

Never calls a live vision API from a request path — this is an offline batch job,
consistent with CLAUDE.md's precompute-first rule. Ollama runs entirely locally
(no hosted API, no cost) so this doesn't reintroduce a live-external-call
dependency into the demo path either way — see app/services/vision.py for the
one place the live API's provider choice is actually made.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from services.vision_classifier import VisionClassifierService  # noqa: E402
from services.vision_providers.mock import MockVisionProvider  # noqa: E402
from services.vision_providers.ollama_provider import OllamaVisionProvider  # noqa: E402

DEFAULT_OUT_PATH = Path("scripts/generated_photos/classification_results.json")


def _build_provider(provider_name: str):
    if provider_name == "mock":
        return MockVisionProvider()
    if provider_name == "ollama":
        return OllamaVisionProvider()
    raise SystemExit(f"unknown provider {provider_name!r}")


def run_manifest_mode(manifest_path: Path, out_path: Path, provider_name: str) -> list[dict]:
    records = json.loads(manifest_path.read_text())
    provider = _build_provider(provider_name)
    service = VisionClassifierService(provider)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for i, rec in enumerate(records, start=1):
        t0 = time.monotonic()
        try:
            kwargs = (
                {"ground_truth_category": rec.get("ground_truth_category"), "is_mismatch": rec.get("is_mismatch_test", False)}
                if provider_name == "mock"
                else {}
            )
            outcome = service.classify(
                image_path=Path(rec["local_path"]),
                declared_category=rec["declared_category"],
                declared_activity=rec["declared_activity"],
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001 -- a real provider (network/model) can fail
            # mid-batch; don't lose every result gathered so far because of one bad record.
            elapsed = time.monotonic() - t0
            print(f"  [{i}/{len(records)} {rec['id']}] FAILED after {elapsed:.1f}s: {exc}", file=sys.stderr)
            results.append(
                {
                    "record_id": rec["id"],
                    "declared_category": rec["declared_category"],
                    "declared_activity": rec["declared_activity"],
                    "is_mismatch_test": rec.get("is_mismatch_test", False),
                    "error": str(exc),
                }
            )
            out_path.write_text(json.dumps(results, indent=2))
            continue

        elapsed = time.monotonic() - t0
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
            f"  [{i}/{len(records)} {rec['id']}] matches={outcome.ai_result['matches_declared']:<9} "
            f"conf={outcome.ai_result['confidence']:.2f}  visual_score={outcome.visual_score:>2}/30  "
            f"({gate})  {elapsed:.1f}s",
            file=sys.stderr,
        )
        # write after every record, not just at the end -- a real provider's
        # per-image latency (real inference can be tens of seconds) makes a
        # mid-batch failure or interruption costly to lose entirely.
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
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"defaults to {DEFAULT_OUT_PATH} for mock, or the same path with "
        f"'_ollama' inserted before the extension for --provider ollama, so the two don't clobber each other",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "ollama"],
        help="'mock' (default, fast/deterministic) or 'ollama' (real local classification via "
        "Ollama — requires `ollama serve` running and the model pulled; see "
        "services/vision_providers/ollama_provider.py)",
    )
    args = parser.parse_args()

    out_path = args.out
    if out_path is None:
        out_path = (
            DEFAULT_OUT_PATH
            if args.provider == "mock"
            else DEFAULT_OUT_PATH.with_name(DEFAULT_OUT_PATH.stem + "_ollama" + DEFAULT_OUT_PATH.suffix)
        )

    if args.db:
        run_db_mode(None)
    else:
        run_manifest_mode(args.manifest, out_path, provider_name=args.provider)


if __name__ == "__main__":
    main()
