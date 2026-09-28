"""
Deterministic stand-in for a live vision LLM.

Exists so the classifier service, FR2.2's confidence-gating logic, and FR2.3's
visual-match scoring can be fully built and pytest-covered without a vision-API
key — none is configured in this environment as of 2026-09-28 (checked
VISION_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY; none
present). See the real-provider stub in anthropic_provider.py for what swaps in
once PRD §14's provider decision + a key are available.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .base import VisionProvider

DEFAULT_MATCH_CONFIDENCE = 0.9
DEFAULT_MISMATCH_CONFIDENCE = 0.85


class MockVisionProvider(VisionProvider):
    """
    Behavior:
      - `force_result`, if given, is returned verbatim on every call — for unit
        tests that need an exact fixture, including deliberately schema-invalid
        dicts, to exercise VisionClassifierService's retry/degrade-to-uncertain
        path.
      - Otherwise, if `is_mismatch=True` is passed at call time, or
        `ground_truth_category` is supplied and differs from `declared_category`,
        returns a confident 'no' (this is what FR2.0's deliberately-mismatched
        photo set is for — see scripts/generate_synthetic_photos.py).
      - Otherwise returns a confident 'yes' matching the declared category/activity.

    `seed` is accepted for API symmetry with a real provider but isn't currently
    used to randomize output — behavior is deliberately deterministic so tests
    are stable.
    """

    name = "mock"

    def __init__(self, *, force_result: dict[str, Any] | None = None, seed: int | None = None):
        self._force_result = force_result
        self._rng = random.Random(seed)

    def classify_raw(
        self,
        image_path: Path,
        declared_category: str,
        declared_activity: str,
        *,
        ground_truth_category: str | None = None,
        is_mismatch: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        if self._force_result is not None:
            return dict(self._force_result)

        mismatch = is_mismatch or (
            ground_truth_category is not None and ground_truth_category != declared_category
        )
        if mismatch:
            return {
                "predicted_category": ground_truth_category or "UNKNOWN",
                "predicted_activity": "a different structure than declared",
                "construction_stage": "completed",
                "water_visible": "unclear",
                "vegetation_cover": "unclear",
                "matches_declared": "no",
                "confidence": DEFAULT_MISMATCH_CONFIDENCE,
                "evidence": "The structure visible in the photo does not match the declared activity.",
            }
        return {
            "predicted_category": declared_category,
            "predicted_activity": declared_activity,
            "construction_stage": "completed",
            "water_visible": "yes",
            "vegetation_cover": "medium",
            "matches_declared": "yes",
            "confidence": DEFAULT_MATCH_CONFIDENCE,
            "evidence": "Structure and surrounding context are consistent with the declared activity.",
        }
