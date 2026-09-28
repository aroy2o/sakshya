"""
pytest coverage for watershed_did.py — R2's watershed-level DiD statistics
(docs/REAL_DATA_PLAN.md §4.1-4.2). Pure functions, no network/GEE.
"""

from __future__ import annotations

import pytest

from watershed_did import (
    AnnualSeries,
    bootstrap_control_polygons,
    dry_season_windows,
    pre_post_effect,
    treated_control_gap,
)


# --- treated_control_gap ------------------------------------------------------

def test_treated_control_gap_basic():
    treated = {2019: 0.5, 2020: 0.6, 2021: 0.7}
    control = {2019: 0.4, 2020: 0.4, 2021: 0.4}
    gap = treated_control_gap(treated, control)
    assert gap == pytest.approx({2019: 0.1, 2020: 0.2, 2021: 0.3})


def test_treated_control_gap_only_common_years():
    treated = {2019: 0.5, 2022: 0.9}
    control = {2019: 0.4, 2020: 0.4}
    gap = treated_control_gap(treated, control)
    assert gap == pytest.approx({2019: 0.1})


# --- pre_post_effect -----------------------------------------------------------

def test_pre_post_effect_positive_effect():
    gap = {2018: 0.1, 2019: 0.1, 2020: 0.1, 2021: 0.3, 2022: 0.3}
    result = pre_post_effect(gap, project_start_year=2021)
    assert result["pre_mean_gap"] == 0.1
    assert result["post_mean_gap"] == 0.3
    assert abs(result["effect"] - 0.2) < 1e-9
    assert result["pre_years"] == [2018, 2019, 2020]
    assert result["post_years"] == [2021, 2022]


def test_pre_post_effect_missing_pre_years():
    gap = {2022: 0.3, 2023: 0.3}
    result = pre_post_effect(gap, project_start_year=2021)
    assert result["effect"] is None
    assert "Insufficient" in result["note"]


def test_pre_post_effect_missing_post_years():
    gap = {2018: 0.1, 2019: 0.1}
    result = pre_post_effect(gap, project_start_year=2021)
    assert result["effect"] is None


def test_pre_post_effect_boundary_year_is_post():
    # project_start_year itself counts as "post" (>=), not "pre" (<)
    gap = {2020: 0.1, 2021: 0.5}
    result = pre_post_effect(gap, project_start_year=2021)
    assert result["pre_years"] == [2020]
    assert result["post_years"] == [2021]


# --- bootstrap_control_polygons -------------------------------------------------

def test_bootstrap_no_controls_returns_none_effect():
    result = bootstrap_control_polygons(
        treated_mean_by_year={2020: 0.5, 2021: 0.6},
        control_series=[],
        project_start_year=2021,
    )
    assert result["effect"] is None
    assert result["ci_low"] is None


def test_bootstrap_deterministic_with_fixed_seed():
    treated = {y: 0.5 for y in range(2018, 2023)}
    controls = [
        AnnualSeries(polygon_id="c1", values_by_year={y: 0.3 for y in range(2018, 2023)}),
        AnnualSeries(polygon_id="c2", values_by_year={y: 0.35 for y in range(2018, 2023)}),
        AnnualSeries(polygon_id="c3", values_by_year={y: 0.25 for y in range(2018, 2023)}),
    ]
    r1 = bootstrap_control_polygons(treated, controls, project_start_year=2021, n_bootstrap=200, seed=7)
    r2 = bootstrap_control_polygons(treated, controls, project_start_year=2021, n_bootstrap=200, seed=7)
    assert r1 == r2


def test_bootstrap_ci_contains_point_effect_when_controls_uniform():
    # All controls identical -> every bootstrap resample gives the same
    # effect as the point estimate -> zero-width CI around it.
    treated = {2019: 0.4, 2020: 0.4, 2021: 0.7, 2022: 0.7}
    controls = [
        AnnualSeries(polygon_id=f"c{i}", values_by_year={2019: 0.3, 2020: 0.3, 2021: 0.3, 2022: 0.3})
        for i in range(5)
    ]
    result = bootstrap_control_polygons(treated, controls, project_start_year=2021, n_bootstrap=500, seed=1)
    assert result["ci_low"] == result["ci_high"] == result["effect"]


def test_bootstrap_ci_widens_with_control_variance():
    # DiD's effect is a *change* (post-mean-gap minus pre-mean-gap), so a
    # control fixture needs varying PRE-TO-POST DELTAS across polygons to
    # produce bootstrap spread — a level shift alone cancels out exactly
    # (that's DiD correctly netting out time-invariant per-polygon offsets).
    treated = {2019: 0.4, 2020: 0.4, 2021: 0.7, 2022: 0.7}
    low_variance = [
        # every control's post-pre delta is identical (0.0) -> zero spread
        AnnualSeries(polygon_id=f"c{i}", values_by_year={2019: 0.30, 2020: 0.30, 2021: 0.30, 2022: 0.30})
        for i in range(6)
    ]
    high_variance = [
        # each control's post-pre delta differs -> resampling which
        # polygons are included changes the average delta -> CI spread
        AnnualSeries(polygon_id=f"c{i}", values_by_year={2019: 0.30, 2020: 0.30, 2021: 0.30 + delta, 2022: 0.30 + delta})
        for i, delta in enumerate([0.0, 0.05, -0.05, 0.15, -0.15, 0.25])
    ]
    r_low = bootstrap_control_polygons(treated, low_variance, project_start_year=2021, n_bootstrap=1000, seed=3)
    r_high = bootstrap_control_polygons(treated, high_variance, project_start_year=2021, n_bootstrap=1000, seed=3)
    width_low = r_low["ci_high"] - r_low["ci_low"]
    width_high = r_high["ci_high"] - r_high["ci_low"]
    assert width_high > width_low


def test_bootstrap_n_control_polygons_recorded():
    treated = {2020: 0.5, 2021: 0.6}
    controls = [AnnualSeries(polygon_id=f"c{i}", values_by_year={2020: 0.3, 2021: 0.3}) for i in range(4)]
    result = bootstrap_control_polygons(treated, controls, project_start_year=2021, n_bootstrap=100, seed=1)
    assert result["n_control_polygons"] == 4


# --- dry_season_windows ---------------------------------------------------------

def test_dry_season_windows_span():
    windows = dry_season_windows(2016, 2018)
    assert len(windows) == 3
    assert windows[0] == {"year": 2016, "start": "2016-11-01", "end": "2017-02-28"}


def test_dry_season_windows_handles_leap_february():
    # 2020 is a leap year -> the dry season starting Nov 2019 ends Feb 2020,
    # and the one starting Nov 2019... check the window whose Feb falls in
    # a leap year (2020 dry season: Nov 2019 -> Feb 2020).
    windows = dry_season_windows(2019, 2019)
    assert windows[0]["end"] == "2020-02-29"


def test_dry_season_windows_non_leap_february():
    windows = dry_season_windows(2021, 2021)
    assert windows[0]["end"] == "2022-02-28"
