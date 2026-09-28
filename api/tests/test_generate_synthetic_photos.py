"""
Sanity check for FR2.0's category/activity table — must only use the fixed PRD
§15.1 codes (AM, VM, SM, PT, NC, BN, LS, LH, OM), never invented ones, and every
mismatch-test record must actually declare a different category than it depicts
(otherwise it wouldn't exercise matches_declared == 'no' at all).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_synthetic_photos import CATEGORY_ACTIVITIES, MISMATCH_SET  # noqa: E402

VALID_CATEGORIES = {"AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"}


def test_good_set_only_uses_prd_15_1_categories():
    assert set(CATEGORY_ACTIVITIES.keys()) == VALID_CATEGORIES


def test_good_set_has_at_least_one_activity_per_category():
    assert all(len(v) >= 1 for v in CATEGORY_ACTIVITIES.values())


def test_good_set_labels_are_short_not_full_prompt_sentences():
    """declared_activity must be a short DRISHTI-style label (PRD §8's
    field_record.activity, e.g. 'Check Dam'), not the long descriptive sentence
    used to drive image generation -- those are two different fields on purpose."""
    for activities in CATEGORY_ACTIVITIES.values():
        for label, description in activities:
            assert len(label) <= 40, f"label too long, looks like a prompt sentence: {label!r}"
            assert len(description) > len(label), "description should be more detailed than the label"


def test_mismatch_set_declared_and_ground_truth_categories_are_valid_and_differ():
    for spec in MISMATCH_SET:
        assert spec["declared_category"] in VALID_CATEGORIES
        assert spec["ground_truth_category"] in VALID_CATEGORIES
        assert spec["declared_category"] != spec["ground_truth_category"], (
            "a mismatch-test record whose declared/ground-truth category are the "
            "same wouldn't actually exercise matches_declared='no'"
        )


def test_mismatch_set_is_non_empty():
    assert len(MISMATCH_SET) >= 1
