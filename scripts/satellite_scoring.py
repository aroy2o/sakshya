"""
Satellite response sub-score computation (PRD §12.3, FR3.5).

Pure functions, NO Earth Engine / GEE dependency — this module never
imports `ee` and is fully testable in isolation without credentials. Given
an activity category and an already-computed DiD result dict, it
classifies the signal into PRD §12.3's four-tier bands and assigns the
0-30 satellite_score.

Threshold constants below are PROVISIONAL. PRD §12.3 defines the four-tier
table (strongly positive / weakly positive / inconclusive / negative) but
not the numeric DiD cutoffs that separate them — that number doesn't exist
anywhere in PRD/PLAYBOOK. These are a hackathon-stage starting point,
flagged for calibration once a real score distribution exists, the same
treatment PRD §12.5 gives its own scoring weights ("provisional... to be
calibrated with DoLR domain experts"). Every value is a named constant,
never a magic number scattered through logic, per CLAUDE.md conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DidClassification(str, Enum):
    STRONGLY_POSITIVE = "strongly_positive"
    WEAKLY_POSITIVE = "weakly_positive"
    INCONCLUSIVE = "inconclusive"
    NEGATIVE = "negative"
    NOT_APPLICABLE = "not_applicable"


# PRD §12.3 point table
SCORE_STRONG = 30
SCORE_WEAK = 18
SCORE_INCONCLUSIVE = 10
SCORE_NEGATIVE = 0
SCORE_NEUTRAL_NO_SIGNAL = 15  # LS, LH, OM — "no reliable satellite signal" (PRD §12.3)

# PRD §12.3's expected-direction table, mapped to which computed index
# actually drives the score for that category.
CATEGORY_PRIMARY_INDEX: dict[str, str | None] = {
    "PT": "water_fraction",   # Pond-Tanks: water extent up and/or NDMI up
    "NC": "water_fraction",   # Nala-Channels: same expectation
    "SM": "water_fraction",   # Structural measures (check dams etc.)
    "VM": "NDVI",             # Vegetative measures: NDVI up
    "AM": "NDVI",             # Agronomic measures: NDVI up
    "BN": "NDVI_NDMI_MEAN",   # Bunds: NDVI/NDMI up in adjoining fields
    "LS": None,                # Livestock — no reliable satellite signal
    "LH": None,                # Livelihood — no reliable satellite signal
    "OM": None,                # Others — no reliable satellite signal
}

NO_SIGNAL_CATEGORIES = frozenset(k for k, v in CATEGORY_PRIMARY_INDEX.items() if v is None)

VALID_CATEGORIES = frozenset(CATEGORY_PRIMARY_INDEX.keys())  # PRD §15.1's fixed set

# Provisional per-index thresholds. A DiD value >= 'strong' -> strongly
# positive; >= 'weak' -> weakly positive; <= -'weak' -> negative;
# otherwise inconclusive. Kept symmetric (weak threshold mirrors the
# negative cutoff) for simplicity at this stage.
THRESHOLDS: dict[str, dict[str, float]] = {
    "NDVI": {"strong": 0.08, "weak": 0.02},
    "NDMI": {"strong": 0.08, "weak": 0.02},
    "MNDWI": {"strong": 0.05, "weak": 0.015},
    "water_fraction": {"strong": 0.15, "weak": 0.05},
    "NDVI_NDMI_MEAN": {"strong": 0.08, "weak": 0.02},
}

_CLASSIFICATION_TO_SCORE = {
    DidClassification.STRONGLY_POSITIVE: SCORE_STRONG,
    DidClassification.WEAKLY_POSITIVE: SCORE_WEAK,
    DidClassification.INCONCLUSIVE: SCORE_INCONCLUSIVE,
    DidClassification.NEGATIVE: SCORE_NEGATIVE,
}


def classify_did(index_name: str, did_value: float) -> DidClassification:
    """Classify a single DiD value into PRD §12.3's four-tier bands."""
    if index_name not in THRESHOLDS:
        raise ValueError(f"No threshold defined for index {index_name!r}")
    t = THRESHOLDS[index_name]
    if did_value >= t["strong"]:
        return DidClassification.STRONGLY_POSITIVE
    if did_value >= t["weak"]:
        return DidClassification.WEAKLY_POSITIVE
    if did_value <= -t["weak"]:
        return DidClassification.NEGATIVE
    return DidClassification.INCONCLUSIVE


@dataclass
class SatelliteScoreResult:
    satellite_score: int
    did_classification: DidClassification
    primary_index_for_category: str | None
    primary_index_did_value: float | None
    notes: list[str] = field(default_factory=list)


def compute_satellite_score(category: str, did: dict[str, float]) -> SatelliteScoreResult:
    """
    PRD §12.3: map a category's DiD result onto the 0-30 satellite_score.

    `did` is the already-computed difference-in-differences dict, e.g.
    {"NDVI": 0.04, "MNDWI": 0.01, "NDMI": 0.02, "water_fraction": 0.2}.
    Missing keys default to 0.0 (treated as no measurable change), except
    the water_fraction -> MNDWI fallback below.
    """
    category = category.upper()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Unknown activity category {category!r} — PRD §15.1 defines "
            "AM/VM/SM/PT/NC/BN/LS/LH/OM only, no others."
        )

    if category in NO_SIGNAL_CATEGORIES:
        return SatelliteScoreResult(
            satellite_score=SCORE_NEUTRAL_NO_SIGNAL,
            did_classification=DidClassification.NOT_APPLICABLE,
            primary_index_for_category=None,
            primary_index_did_value=None,
            notes=[
                f"Category {category}: satellite evidence is not meaningful for this "
                "activity type (PRD §12.3) — neutral score applied, not computed from data."
            ],
        )

    primary_index = CATEGORY_PRIMARY_INDEX[category]
    assert primary_index is not None  # narrowed by the NO_SIGNAL_CATEGORIES check above

    if primary_index == "NDVI_NDMI_MEAN":
        value = (did.get("NDVI", 0.0) + did.get("NDMI", 0.0)) / 2.0
    elif primary_index == "water_fraction" and "water_fraction" not in did:
        # No direct water-pixel-fraction figure computed (e.g. real-GEE path
        # didn't run water_fraction()) — fall back to MNDWI as the water proxy.
        primary_index = "MNDWI"
        value = did.get("MNDWI", 0.0)
    else:
        value = did.get(primary_index, 0.0)

    classification = classify_did(primary_index, value)
    score = _CLASSIFICATION_TO_SCORE[classification]

    notes: list[str] = []
    if classification == DidClassification.NEGATIVE:
        notes.append(
            "Negative DiD relative to control — flagged for review. This can also mean "
            "'too early post-work' rather than failure; not a definitive verdict (PRD §12.3)."
        )

    return SatelliteScoreResult(
        satellite_score=score,
        did_classification=classification,
        primary_index_for_category=primary_index,
        primary_index_did_value=value,
        notes=notes,
    )
