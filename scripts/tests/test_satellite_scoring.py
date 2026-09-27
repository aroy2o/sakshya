"""
pytest coverage for satellite_scoring.py — FR3.5, PRD §12.3.

This is the module CLAUDE.md's testing convention most directly targets
for Phase 3 ("pytest for backend logic, *especially* the geo-integrity
validator and scoring engine — these need to be provably correct against
the rules in PRD.md §12"). satellite_scoring has no GEE dependency, so
every rule in §12.3's table is checked exactly, at its boundaries.
"""

from __future__ import annotations

import pytest

from satellite_scoring import (
    CATEGORY_PRIMARY_INDEX,
    NO_SIGNAL_CATEGORIES,
    SCORE_NEGATIVE,
    SCORE_NEUTRAL_NO_SIGNAL,
    SCORE_STRONG,
    SCORE_WEAK,
    SCORE_INCONCLUSIVE,
    THRESHOLDS,
    DidClassification,
    classify_did,
    compute_satellite_score,
)


# --- classify_did: boundary behaviour per index ------------------------------

@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_at_strong_boundary_is_strongly_positive(index_name):
    t = THRESHOLDS[index_name]
    assert classify_did(index_name, t["strong"]) == DidClassification.STRONGLY_POSITIVE
    assert classify_did(index_name, t["strong"] + 1.0) == DidClassification.STRONGLY_POSITIVE


@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_just_below_strong_is_weakly_positive(index_name):
    t = THRESHOLDS[index_name]
    epsilon = 1e-6
    assert classify_did(index_name, t["strong"] - epsilon) == DidClassification.WEAKLY_POSITIVE


@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_at_weak_boundary_is_weakly_positive(index_name):
    t = THRESHOLDS[index_name]
    assert classify_did(index_name, t["weak"]) == DidClassification.WEAKLY_POSITIVE


@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_zero_is_inconclusive(index_name):
    assert classify_did(index_name, 0.0) == DidClassification.INCONCLUSIVE


@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_just_inside_negative_boundary_is_inconclusive(index_name):
    t = THRESHOLDS[index_name]
    epsilon = 1e-6
    assert classify_did(index_name, -t["weak"] + epsilon) == DidClassification.INCONCLUSIVE


@pytest.mark.parametrize("index_name", list(THRESHOLDS.keys()))
def test_classify_did_at_negative_boundary_is_negative(index_name):
    t = THRESHOLDS[index_name]
    assert classify_did(index_name, -t["weak"]) == DidClassification.NEGATIVE
    assert classify_did(index_name, -t["weak"] - 1.0) == DidClassification.NEGATIVE


def test_classify_did_unknown_index_raises():
    with pytest.raises(ValueError):
        classify_did("NOT_A_REAL_INDEX", 0.5)


# --- compute_satellite_score: category routing per PRD §12.3's table --------

@pytest.mark.parametrize("category", ["PT", "NC", "SM"])
def test_water_categories_score_strong_on_big_water_gain(category):
    result = compute_satellite_score(category, {"water_fraction": 0.30})
    assert result.satellite_score == SCORE_STRONG
    assert result.did_classification == DidClassification.STRONGLY_POSITIVE
    assert result.primary_index_for_category == "water_fraction"


@pytest.mark.parametrize("category", ["VM", "AM"])
def test_vegetative_categories_use_ndvi(category):
    result = compute_satellite_score(category, {"NDVI": 0.10, "water_fraction": 0.9})
    # water_fraction present but irrelevant for VM/AM — must route on NDVI only
    assert result.primary_index_for_category == "NDVI"
    assert result.satellite_score == SCORE_STRONG


def test_bn_uses_mean_of_ndvi_and_ndmi():
    result = compute_satellite_score("BN", {"NDVI": 0.10, "NDMI": 0.06})
    assert result.primary_index_for_category == "NDVI_NDMI_MEAN"
    assert result.primary_index_did_value == pytest.approx(0.08)
    assert result.did_classification == DidClassification.STRONGLY_POSITIVE
    assert result.satellite_score == SCORE_STRONG


@pytest.mark.parametrize("category", sorted(NO_SIGNAL_CATEGORIES))
def test_no_signal_categories_are_always_neutral(category):
    # Even a strongly positive-looking did dict must not move the score —
    # LS/LH/OM are defined as "no reliable satellite signal" (PRD §12.3).
    result = compute_satellite_score(category, {"NDVI": 0.99, "water_fraction": 0.99})
    assert result.satellite_score == SCORE_NEUTRAL_NO_SIGNAL
    assert result.did_classification == DidClassification.NOT_APPLICABLE
    assert result.primary_index_for_category is None
    assert result.notes  # must explain why, not silently return 15


def test_no_signal_categories_cover_ls_lh_om_exactly():
    assert NO_SIGNAL_CATEGORIES == frozenset({"LS", "LH", "OM"})


def test_water_fraction_falls_back_to_mndwi_when_absent():
    result = compute_satellite_score("PT", {"MNDWI": 0.06})
    assert result.primary_index_for_category == "MNDWI"
    assert result.did_classification == DidClassification.STRONGLY_POSITIVE
    assert result.satellite_score == SCORE_STRONG


def test_missing_index_defaults_to_zero_and_is_inconclusive():
    result = compute_satellite_score("VM", {})
    assert result.primary_index_did_value == 0.0
    assert result.did_classification == DidClassification.INCONCLUSIVE
    assert result.satellite_score == SCORE_INCONCLUSIVE


def test_negative_did_scores_zero_and_carries_a_caveat_note():
    result = compute_satellite_score("VM", {"NDVI": -0.10})
    assert result.satellite_score == SCORE_NEGATIVE
    assert result.did_classification == DidClassification.NEGATIVE
    assert result.notes, "negative classification must carry a caveat note (PRD §12.3)"
    assert "too early" in result.notes[0].lower()


def test_weak_positive_scores_18():
    result = compute_satellite_score("VM", {"NDVI": 0.03})
    assert result.satellite_score == SCORE_WEAK
    assert result.did_classification == DidClassification.WEAKLY_POSITIVE


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        compute_satellite_score("ZZ", {"NDVI": 0.5})


def test_category_case_insensitive():
    result = compute_satellite_score("vm", {"NDVI": 0.5})
    assert result.satellite_score == SCORE_STRONG


def test_all_prd_categories_are_covered():
    # PRD §15.1's fixed activity-category table, verbatim.
    assert set(CATEGORY_PRIMARY_INDEX.keys()) == {
        "AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"
    }
