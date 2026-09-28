"""
Tests for the vision classifier service (PRD Phase 2: FR2.1-FR2.3): the strict
enum-only schema, the §12.2 visual-match scoring table (including its one
undocumented boundary — see vision_classifier.compute_visual_score's comment),
and the FR2.2 confidence-gating rule. All run against MockVisionProvider — no
vision API key required, none is configured in this environment.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from services.vision_classifier import (
    ClassifierResult,
    MatchResult,
    VisionClassifierService,
    compute_flags,
    compute_needs_review,
    compute_visual_score,
)
from services.vision_providers.mock import MockVisionProvider

DUMMY_IMAGE_PATH = Path("unused/for/mock.jpg")  # MockVisionProvider never touches disk


# ---------------------------------------------------------------------------
# FR2.3 -- PRD §12.2's visual-match scoring table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "matches_declared,confidence,expected_score",
    [
        (MatchResult.YES, 0.75, 30),
        (MatchResult.YES, 1.0, 30),
        (MatchResult.YES, 0.9, 30),
        (MatchResult.YES, 0.7499, 20),  # just below the high-confidence cutoff
        (MatchResult.YES, 0.5, 20),
        (MatchResult.YES, 0.6, 20),
        (MatchResult.YES, 0.4999, 10),  # documented gap-fill below the table's floor
        (MatchResult.YES, 0.0, 10),
        (MatchResult.UNCERTAIN, 0.0, 10),
        (MatchResult.UNCERTAIN, 0.95, 10),  # confidence is irrelevant for 'uncertain'
        (MatchResult.NO, 0.0, 0),
        (MatchResult.NO, 0.99, 0),  # confidence is irrelevant for 'no'
    ],
)
def test_visual_score_matches_prd_12_2_table(matches_declared, confidence, expected_score):
    assert compute_visual_score(matches_declared, confidence) == expected_score


# ---------------------------------------------------------------------------
# FR2.2 -- confidence gating (< 0.6 or 'uncertain' -> needs_review)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "matches_declared,confidence,expected_gate",
    [
        (MatchResult.YES, 0.6, False),  # exactly at the gate -> not gated
        (MatchResult.YES, 0.5999, True),  # just below -> gated
        (MatchResult.YES, 0.75, False),
        (MatchResult.YES, 0.0, True),
        (MatchResult.UNCERTAIN, 0.99, True),  # uncertain always gates, confidence irrelevant
        (MatchResult.NO, 0.99, False),  # literal FR2.2 text: NO only gates via confidence
        (MatchResult.NO, 0.3, True),
    ],
)
def test_confidence_gating_matches_fr2_2(matches_declared, confidence, expected_gate):
    assert compute_needs_review(matches_declared, confidence) is expected_gate


def test_gate_can_disagree_with_a_decent_visual_score():
    """The exact scenario flagged to the coordinator: matches_declared=yes with
    confidence=0.55 scores 20/30 on the table (not the bottom bracket) but is
    still below the 0.6 review gate. Per the coordinator's 2026-09-28 decision,
    backend-engineer's services/scoring.py (FR4.1) must treat needs_review as a
    hard band-capping override regardless of this decent sub-score."""
    score = compute_visual_score(MatchResult.YES, 0.55)
    gated = compute_needs_review(MatchResult.YES, 0.55)
    assert score == 20
    assert gated is True


# ---------------------------------------------------------------------------
# flags
# ---------------------------------------------------------------------------


def test_no_match_raises_activity_mismatch_flag():
    flags = compute_flags(MatchResult.NO, needs_review=False)
    assert "activity_mismatch" in flags


def test_uncertain_raises_review_flag_distinct_from_low_confidence():
    flags = compute_flags(MatchResult.UNCERTAIN, needs_review=True)
    assert "uncertain_match_review" in flags
    assert "low_confidence_review" not in flags


def test_no_match_below_gate_gets_both_flags():
    flags = compute_flags(MatchResult.NO, needs_review=True)
    assert "activity_mismatch" in flags
    assert "low_confidence_review" in flags


# ---------------------------------------------------------------------------
# strict enum-only schema
# ---------------------------------------------------------------------------


def test_schema_rejects_invented_category():
    with pytest.raises(ValidationError):
        ClassifierResult.model_validate(
            {
                "predicted_category": "XX",  # not in PRD §15.1
                "predicted_activity": "something",
                "construction_stage": "completed",
                "water_visible": "yes",
                "vegetation_cover": "medium",
                "matches_declared": "yes",
                "confidence": 0.9,
                "evidence": "test",
            }
        )


def test_schema_rejects_value_outside_enum():
    with pytest.raises(ValidationError):
        ClassifierResult.model_validate(
            {
                "predicted_category": "SM",
                "predicted_activity": "check dam",
                "construction_stage": "mostly finished",  # not a valid enum value
                "water_visible": "yes",
                "vegetation_cover": "medium",
                "matches_declared": "yes",
                "confidence": 0.9,
                "evidence": "test",
            }
        )


def test_schema_forbids_extra_fields():
    with pytest.raises(ValidationError):
        ClassifierResult.model_validate(
            {
                "predicted_category": "SM",
                "predicted_activity": "check dam",
                "construction_stage": "completed",
                "water_visible": "yes",
                "vegetation_cover": "medium",
                "matches_declared": "yes",
                "confidence": 0.9,
                "evidence": "test",
                "extra_free_text_field": "the model should not be able to sneak this in",
            }
        )


def test_schema_rejects_confidence_outside_0_1():
    with pytest.raises(ValidationError):
        ClassifierResult.model_validate(
            {
                "predicted_category": "SM",
                "predicted_activity": "check dam",
                "construction_stage": "completed",
                "water_visible": "yes",
                "vegetation_cover": "medium",
                "matches_declared": "yes",
                "confidence": 1.5,
                "evidence": "test",
            }
        )


# ---------------------------------------------------------------------------
# end-to-end service behavior against the mock provider
# ---------------------------------------------------------------------------


def test_service_end_to_end_confident_match():
    service = VisionClassifierService(MockVisionProvider())
    outcome = service.classify(
        image_path=DUMMY_IMAGE_PATH,
        declared_category="SM",
        declared_activity="Check Dam",
    )
    assert outcome.visual_score == 30
    assert outcome.ai_result["needs_review"] is False
    assert outcome.ai_result["matches_declared"] == "yes"
    assert outcome.ai_result["provider"] == "mock"
    assert outcome.ai_result["flags"] == []


def test_service_end_to_end_deliberate_mismatch():
    service = VisionClassifierService(MockVisionProvider())
    outcome = service.classify(
        image_path=DUMMY_IMAGE_PATH,
        declared_category="SM",
        declared_activity="Check Dam",
        ground_truth_category="VM",
        is_mismatch=True,
    )
    assert outcome.visual_score == 0
    assert "activity_mismatch" in outcome.ai_result["flags"]
    assert outcome.ai_result["matches_declared"] == "no"


def test_service_degrades_to_uncertain_on_malformed_provider_response():
    """A provider returning a schema-invalid dict must never be passed through
    or guessed at -- it degrades to an explicit 'uncertain' result with
    confidence 0.0, never silently fabricated data (CLAUDE.md: 'never fabricate
    a number')."""
    bad_provider = MockVisionProvider(force_result={"predicted_category": "NOT_REAL"})
    service = VisionClassifierService(bad_provider, max_retries=0)
    outcome = service.classify(
        image_path=DUMMY_IMAGE_PATH,
        declared_category="SM",
        declared_activity="Check Dam",
    )
    assert outcome.ai_result["matches_declared"] == "uncertain"
    assert outcome.ai_result["confidence"] == 0.0
    assert outcome.ai_result["needs_review"] is True
    assert outcome.visual_score == 10
    assert "invalid classifier response" in outcome.ai_result["predicted_activity"]
