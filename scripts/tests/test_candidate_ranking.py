"""
pytest coverage for candidate_ranking.py — R1's automated treated/control
micro-watershed ranking (docs/REAL_DATA_PLAN.md §1, §4.1, §9 item 2). Pure
functions, no network — mirrors test_satellite_scoring.py's pattern of
checking documented thresholds at their exact boundaries.
"""

from __future__ import annotations

from candidate_ranking import (
    CONTROL_CROP_SHARE_TOLERANCE,
    CONTROL_SLOPE_TOLERANCE_DEG,
    MAX_AREA_HA,
    MAX_BUILT_UP_SHARE,
    MAX_WATER_SHARE,
    MIN_AREA_HA,
    PICK_METHOD,
    CandidateMetrics,
    RankedCandidate,
    composite_score,
    in_preferred_slope_band,
    match_controls,
    passes_exclusion,
    rank_candidates,
    select_treated,
)


def _m(id="c1", area_ha=1000.0, crop=0.5, built=0.05, water=0.05, tree=0.3, slope=4.0, district="Marigaon", pixel_count=100):
    return CandidateMetrics(
        id=id,
        mws_code=f"MWS-{id}",
        district=district,
        area_ha=area_ha,
        crop_share=crop,
        built_up_share=built,
        water_share=water,
        tree_share=tree,
        mean_slope_deg=slope,
        pixel_count=pixel_count,
    )


# --- passes_exclusion --------------------------------------------------------

def test_passes_exclusion_ok_candidate():
    ok, reason = passes_exclusion(_m())
    assert ok is True
    assert reason is None


def test_passes_exclusion_no_pixels_excluded():
    ok, reason = passes_exclusion(_m(pixel_count=0))
    assert ok is False
    assert "pixel" in reason


def test_passes_exclusion_too_small_area():
    ok, reason = passes_exclusion(_m(area_ha=MIN_AREA_HA - 1))
    assert ok is False
    assert "area_ha" in reason


def test_passes_exclusion_too_large_area():
    ok, reason = passes_exclusion(_m(area_ha=MAX_AREA_HA + 1))
    assert ok is False


def test_passes_exclusion_area_at_boundaries_ok():
    assert passes_exclusion(_m(area_ha=MIN_AREA_HA))[0] is True
    assert passes_exclusion(_m(area_ha=MAX_AREA_HA))[0] is True


def test_passes_exclusion_built_up_over_threshold():
    ok, reason = passes_exclusion(_m(built=MAX_BUILT_UP_SHARE + 0.001))
    assert ok is False
    assert "built_up_share" in reason


def test_passes_exclusion_built_up_at_threshold_ok():
    assert passes_exclusion(_m(built=MAX_BUILT_UP_SHARE))[0] is True


def test_passes_exclusion_water_over_threshold():
    ok, reason = passes_exclusion(_m(water=MAX_WATER_SHARE + 0.001))
    assert ok is False
    assert "water_share" in reason


def test_passes_exclusion_water_at_threshold_ok():
    assert passes_exclusion(_m(water=MAX_WATER_SHARE))[0] is True


# --- composite_score ---------------------------------------------------------

def test_composite_score_higher_crop_share_scores_higher():
    low = composite_score(_m(crop=0.2, built=0.05, water=0.05))
    high = composite_score(_m(crop=0.8, built=0.05, water=0.05))
    assert high > low


def test_composite_score_higher_built_up_scores_lower():
    low_built = composite_score(_m(built=0.05))
    high_built = composite_score(_m(built=0.14))
    assert low_built > high_built


def test_composite_score_higher_water_scores_lower():
    low_water = composite_score(_m(water=0.05))
    high_water = composite_score(_m(water=0.29))
    assert low_water > high_water


def test_composite_score_bounded_0_to_1():
    # crop_share/built_up/water are all in [0,1] and weights sum to 1.0
    best = composite_score(_m(crop=1.0, built=0.0, water=0.0))
    worst = composite_score(_m(crop=0.0, built=1.0, water=1.0))
    assert best == 1.0
    assert worst == 0.0


# --- in_preferred_slope_band --------------------------------------------------

def test_slope_band_none_when_missing():
    assert in_preferred_slope_band(None) is None


def test_slope_band_true_inside():
    assert in_preferred_slope_band(4.0) is True


def test_slope_band_false_outside():
    assert in_preferred_slope_band(0.5) is False
    assert in_preferred_slope_band(9.0) is False


# --- rank_candidates / select_treated -----------------------------------------

def test_rank_candidates_orders_by_score_descending():
    cands = [_m(id="low", crop=0.2), _m(id="high", crop=0.9), _m(id="mid", crop=0.5)]
    ranked = rank_candidates(cands)
    eligible = sorted([r for r in ranked if not r.excluded], key=lambda r: r.rank)
    assert [r.id for r in eligible] == ["high", "mid", "low"]
    assert eligible[0].rank == 1


def test_rank_candidates_excluded_have_no_rank():
    cands = [_m(id="ok"), _m(id="bad", built=0.9)]
    ranked = rank_candidates(cands)
    bad = next(r for r in ranked if r.id == "bad")
    assert bad.excluded is True
    assert bad.rank is None
    assert bad.exclusion_reason is not None


def test_select_treated_returns_top_k_only():
    cands = [_m(id=f"c{i}", crop=i / 10) for i in range(10)]
    ranked = rank_candidates(cands)
    top3 = select_treated(ranked, top_k=3)
    assert len(top3) == 3
    assert [c.rank for c in top3] == [1, 2, 3]


def test_select_treated_never_returns_excluded():
    cands = [_m(id="ok", crop=0.9), _m(id="bad", crop=0.99, built=0.9)]
    ranked = rank_candidates(cands)
    top = select_treated(ranked, top_k=5)
    assert all(not c.excluded for c in top)
    assert "bad" not in [c.id for c in top]


# --- match_controls ------------------------------------------------------------

def test_match_controls_labels_ndvi_pending_gee():
    treated = [_m(id="t1", crop=0.5, slope=4.0)]
    pool = rank_candidates([_m(id="p1", crop=0.52, slope=4.5, district="Nagaon")])
    matches = match_controls(treated, pool, treated_ids={"t1"})
    assert len(matches) == 1
    assert matches[0]["ndvi_match"] == "pending_gee"


def test_match_controls_excludes_treated_ids():
    treated = [_m(id="t1", crop=0.5, slope=4.0)]
    pool = rank_candidates([_m(id="t1", crop=0.5, slope=4.0, district="Marigaon")])
    matches = match_controls(treated, pool, treated_ids={"t1"})
    assert matches == []


def test_match_controls_respects_crop_share_tolerance():
    treated = [_m(id="t1", crop=0.5, slope=4.0)]
    within = _m(id="p_within", crop=0.5 * (1 + CONTROL_CROP_SHARE_TOLERANCE - 0.01), slope=4.0, district="Nagaon")
    outside = _m(id="p_outside", crop=0.5 * (1 + CONTROL_CROP_SHARE_TOLERANCE + 0.10), slope=4.0, district="Nagaon")
    pool = rank_candidates([within, outside])
    matches = match_controls(treated, pool, treated_ids={"t1"})
    ids = [m["id"] for m in matches]
    assert "p_within" in ids
    assert "p_outside" not in ids


def test_match_controls_respects_slope_tolerance():
    treated = [_m(id="t1", crop=0.5, slope=4.0)]
    within = _m(id="p_within", crop=0.5, slope=4.0 + CONTROL_SLOPE_TOLERANCE_DEG - 0.5, district="Nagaon")
    outside = _m(id="p_outside", crop=0.5, slope=4.0 + CONTROL_SLOPE_TOLERANCE_DEG + 2.0, district="Nagaon")
    pool = rank_candidates([within, outside])
    matches = match_controls(treated, pool, treated_ids={"t1"})
    ids = [m["id"] for m in matches]
    assert "p_within" in ids
    assert "p_outside" not in ids


def test_match_controls_excludes_pool_entries_that_fail_exclusion():
    treated = [_m(id="t1", crop=0.5, slope=4.0)]
    pool = rank_candidates([_m(id="p_bad", crop=0.5, slope=4.0, built=0.9, district="Nagaon")])
    matches = match_controls(treated, pool, treated_ids={"t1"})
    assert matches == []


def test_match_controls_empty_treated_returns_empty():
    pool = rank_candidates([_m(id="p1")])
    assert match_controls([], pool, treated_ids=set()) == []


def test_pick_method_constant_is_stable_string():
    # Guards against an accidental rename — every downstream JSON output
    # keys off this exact string (REAL_DATA_PLAN.md §9 item 2 labelling
    # requirement).
    assert PICK_METHOD == "automated_ranking_pending_human_confirmation"
