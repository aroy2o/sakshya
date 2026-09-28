"""
AI Image Interpreter — vision classifier service (PRD Phase 2: FR2.1, FR2.2, FR2.3).

Scope discipline (PRD §12.2, restated because it's easy to blur in code): this
module answers "is this photo evidence of the declared activity?" only. It never
looks at satellite/NDVI data and nothing here computes or influences
satellite_score — that question belongs entirely to geospatial-engineer's
territory (PRD §12.3).

Everything below is buildable and pytest-covered without a live vision-API key —
none is configured in this environment (see anthropic_provider.py's docstring).
Swap MockVisionProvider for a real VisionProvider once PRD §14's provider
decision lands; nothing else in this module needs to change.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from services.vision_providers.base import VisionProvider, VisionProviderError

# ---------------------------------------------------------------------------
# Fixed enums. predicted_category is locked to PRD §15.1's 9 codes (+ UNKNOWN,
# for "doesn't look like any of these") — never invent a new category here.
# The other enums come straight from PLAYBOOK.md §8.3's starter prompt.
# ---------------------------------------------------------------------------


class ActivityCategory(str, Enum):
    AM = "AM"
    VM = "VM"
    SM = "SM"
    PT = "PT"
    NC = "NC"
    BN = "BN"
    LS = "LS"
    LH = "LH"
    OM = "OM"
    UNKNOWN = "UNKNOWN"


class ConstructionStage(str, Enum):
    NOT_STARTED = "not_started"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    DAMAGED = "damaged"
    UNCLEAR = "unclear"


class TriState(str, Enum):
    """Used for water_visible: yes / no / unclear."""

    YES = "yes"
    NO = "no"
    UNCLEAR = "unclear"


class VegetationCover(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNCLEAR = "unclear"


class MatchResult(str, Enum):
    YES = "yes"
    NO = "no"
    UNCERTAIN = "uncertain"


# ---------------------------------------------------------------------------
# Strict enum-only response schema. extra="forbid" rejects any field the model
# tries to sneak in beyond this list — "strict enum-only JSON output, never
# free-text" (root CLAUDE.md) is enforced here, not just requested in the prompt.
# ---------------------------------------------------------------------------


class ClassifierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_category: ActivityCategory
    predicted_activity: str = Field(min_length=1, max_length=200)
    construction_stage: ConstructionStage
    water_visible: TriState
    vegetation_cover: VegetationCover
    matches_declared: MatchResult
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1, max_length=500)


class AiResult(ClassifierResult):
    """What actually gets stored in asset_evidence.ai_result (JSONB, PRD §8).
    Adds the FR2.2 gating outcome, derived flags, and provenance on top of the
    raw classifier fields — asset_evidence.visual_score is stored separately
    (see ClassificationOutcome) since it's its own INT column, not nested here."""

    needs_review: bool
    flags: list[str] = Field(default_factory=list)
    provider: str
    model: str | None = None
    classified_at: datetime


@dataclass(frozen=True)
class ClassificationOutcome:
    ai_result: dict[str, Any]  # JSON-serializable -> asset_evidence.ai_result
    visual_score: int  # 0-30 -> asset_evidence.visual_score


# ---------------------------------------------------------------------------
# FR2.3 — visual-match sub-score, PRD §12.2's table exactly, as named constants
# (not scattered magic numbers), matching the convention §12.5 mandates for
# services/scoring.py.
# ---------------------------------------------------------------------------

CONFIDENCE_HIGH = 0.75  # matches_declared=yes & confidence >= this -> full marks
CONFIDENCE_MEDIUM = 0.5  # matches_declared=yes & confidence >= this -> partial marks
CONFIDENCE_REVIEW_GATE = 0.6  # FR2.2: confidence < this -> needs_review, any matches_declared

VISUAL_SCORE_MAX = 30
VISUAL_SCORE_YES_HIGH = 30
VISUAL_SCORE_YES_MEDIUM = 20
VISUAL_SCORE_UNCERTAIN = 10
VISUAL_SCORE_NO = 0
# PRD §12.2's table doesn't define matches_declared == 'yes' with confidence < 0.5
# (the table only gives >=0.75 and 0.5-0.75 brackets for 'yes'). Documented
# gap-fill, flagged to the human rather than silently decided: treat it the same
# as the 'uncertain' bucket, not the same as a firm 'no' — the model did assert a
# positive match, it's just not confident, which is closer in spirit to
# "uncertain" than to an explicit mismatch. It is always needs_review-gated
# anyway, since confidence < 0.6 in this branch.
VISUAL_SCORE_YES_LOW_CONFIDENCE = VISUAL_SCORE_UNCERTAIN


def compute_visual_score(matches_declared: MatchResult, confidence: float) -> int:
    """PRD §12.2's table. Pure function, no I/O — the exact thing worth a
    boundary-case pytest, not a vibe check."""
    if matches_declared is MatchResult.YES:
        if confidence >= CONFIDENCE_HIGH:
            return VISUAL_SCORE_YES_HIGH
        if confidence >= CONFIDENCE_MEDIUM:
            return VISUAL_SCORE_YES_MEDIUM
        return VISUAL_SCORE_YES_LOW_CONFIDENCE
    if matches_declared is MatchResult.UNCERTAIN:
        return VISUAL_SCORE_UNCERTAIN
    return VISUAL_SCORE_NO  # matches_declared is MatchResult.NO


def compute_needs_review(matches_declared: MatchResult, confidence: float) -> bool:
    """FR2.2, literal PRD text: 'confidence < 0.6 or matches_declared == uncertain
    -> band nudged toward review regardless of numeric score.'

    Coordinator-approved 2026-09-28: this is an existing PRD requirement, not a
    new scoring-formula decision requiring separate sign-off. backend-engineer's
    services/scoring.py (FR4.1) must treat this flag as a hard band-capping
    override — when True, band is forced to 'review' even if the raw sub-score
    sum would reach 70+. This function only produces the flag; enforcing it in
    the band formula is backend-engineer's side of the handoff."""
    return confidence < CONFIDENCE_REVIEW_GATE or matches_declared is MatchResult.UNCERTAIN


def compute_flags(matches_declared: MatchResult, needs_review: bool) -> list[str]:
    """Parallel in spirit to geo_flags (PRD §8), but scoped inside ai_result's
    JSONB blob since §8 has no separate visual-flags column."""
    flags: list[str] = []
    if matches_declared is MatchResult.NO:
        flags.append("activity_mismatch")
    if needs_review:
        flags.append(
            "uncertain_match_review" if matches_declared is MatchResult.UNCERTAIN else "low_confidence_review"
        )
    return flags


# ---------------------------------------------------------------------------
# FR2.1 — prompt template, parameterized version of PLAYBOOK.md §8.3's starter
# prompt. Used by real providers (see anthropic_provider.py); MockVisionProvider
# doesn't need it, since it never actually calls out to a model.
# ---------------------------------------------------------------------------


def build_classifier_prompt(declared_category: str, declared_activity: str) -> str:
    categories = ", ".join(c.value for c in ActivityCategory if c is not ActivityCategory.UNKNOWN)
    return f"""You are verifying a watershed field photo from India's WDC-PMKSY programme.
Declared activity: "{declared_activity}" (category {declared_category}).
Return ONLY JSON:
{{"predicted_category": one of [{categories},UNKNOWN],
 "predicted_activity": short label,
 "construction_stage": one of [not_started, under_construction, completed, damaged, unclear],
 "water_visible": one of [yes, no, unclear],
 "vegetation_cover": one of [low, medium, high, unclear],
 "matches_declared": one of [yes, no, uncertain],
 "confidence": 0.0-1.0,
 "evidence": "one sentence describing what in the image supports this"}}
If the image is unclear, blurry, or not a field scene, use "unclear"/"uncertain" — do not guess."""


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_FALLBACK_REASON_MAX_LEN = 400


class VisionClassifierService:
    """FR2.1's classifier service. Provider-agnostic — pass MockVisionProvider
    today, swap in a real VisionProvider once PRD §14's choice + key exist,
    nothing else here changes."""

    def __init__(self, provider: VisionProvider, *, max_retries: int = 1):
        self.provider = provider
        self.max_retries = max_retries

    def classify(
        self,
        image_path: Path | str,
        declared_category: str,
        declared_activity: str,
        **provider_kwargs: Any,
    ) -> ClassificationOutcome:
        result = self._get_validated_result(
            Path(image_path), declared_category, declared_activity, **provider_kwargs
        )
        needs_review = compute_needs_review(result.matches_declared, result.confidence)
        visual_score = compute_visual_score(result.matches_declared, result.confidence)
        flags = compute_flags(result.matches_declared, needs_review)

        ai_result = AiResult(
            **result.model_dump(),
            needs_review=needs_review,
            flags=flags,
            provider=self.provider.name,
            model=getattr(self.provider, "model", None),
            classified_at=datetime.now(timezone.utc),
        )
        return ClassificationOutcome(
            ai_result=json.loads(ai_result.model_dump_json()),
            visual_score=visual_score,
        )

    def _get_validated_result(
        self,
        image_path: Path,
        declared_category: str,
        declared_activity: str,
        **provider_kwargs: Any,
    ) -> ClassifierResult:
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                raw = self.provider.classify_raw(
                    image_path, declared_category, declared_activity, **provider_kwargs
                )
                return ClassifierResult.model_validate(raw)
            except (ValidationError, VisionProviderError) as exc:
                last_error = exc
        # Retries exhausted: never fabricate a guess (CLAUDE.md — "never
        # fabricate a number" applies to classifier output too, not just
        # scoring numbers). Degrade to an explicit, honestly-labelled
        # 'uncertain' result instead of passing through malformed data.
        reason = str(last_error)[:_FALLBACK_REASON_MAX_LEN] if last_error else "unknown error"
        return ClassifierResult(
            predicted_category=ActivityCategory.UNKNOWN,
            predicted_activity="unclassified (invalid classifier response)",
            construction_stage=ConstructionStage.UNCLEAR,
            water_visible=TriState.UNCLEAR,
            vegetation_cover=VegetationCover.UNCLEAR,
            matches_declared=MatchResult.UNCERTAIN,
            confidence=0.0,
            evidence=f"Classifier response invalid after {self.max_retries + 1} attempt(s): {reason}",
        )
