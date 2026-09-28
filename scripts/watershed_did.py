"""
R2 — docs/REAL_DATA_PLAN.md §4.1-4.2. Watershed-level difference-in-
differences: treated micro-watershed(s) vs. a matched pool of control
micro-watersheds, bootstrapped over WHICH control polygons are included
(not over years — the plan's own wording: "a bootstrap interval over
control polygons").

Pure functions, NO Earth Engine dependency — mirrors satellite_scoring.py's
separation of pure scoring/statistics from I/O (gee_client.py /
precompute_watershed_timeseries.py do the actual data pulls). Fully
unit-testable without credentials or network.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field


DEFAULT_N_BOOTSTRAP = 2000
DEFAULT_CI = 0.95  # 95% interval — no PRD/plan source for this exact number;
# a conventional default, documented as such (same treatment every other
# provisional constant in this codebase gets).


@dataclass
class AnnualSeries:
    """year -> value, for one polygon (treated union or one control)."""

    polygon_id: str
    values_by_year: dict[int, float]


def treated_control_gap(
    treated_mean_by_year: dict[int, float], control_mean_by_year: dict[int, float]
) -> dict[int, float]:
    """Per-year (treated - control) gap, only for years present in both."""
    return {
        year: treated_mean_by_year[year] - control_mean_by_year[year]
        for year in treated_mean_by_year
        if year in control_mean_by_year
    }


def pre_post_effect(gap_by_year: dict[int, float], project_start_year: int) -> dict:
    """
    REAL_DATA_PLAN.md §4.2: "Effect = change in the treated–control gap,
    pre vs post [project start]." pre = mean gap for years < project_start_year;
    post = mean gap for years >= project_start_year. effect = post - pre.
    """
    pre_years = sorted(y for y in gap_by_year if y < project_start_year)
    post_years = sorted(y for y in gap_by_year if y >= project_start_year)
    if not pre_years or not post_years:
        return {
            "pre_mean_gap": None,
            "post_mean_gap": None,
            "effect": None,
            "pre_years": pre_years,
            "post_years": post_years,
            "note": "Insufficient years on one side of project_start_year to compute an effect.",
        }
    pre_mean = statistics.mean(gap_by_year[y] for y in pre_years)
    post_mean = statistics.mean(gap_by_year[y] for y in post_years)
    return {
        "pre_mean_gap": pre_mean,
        "post_mean_gap": post_mean,
        "effect": post_mean - pre_mean,
        "pre_years": pre_years,
        "post_years": post_years,
    }


def bootstrap_control_polygons(
    treated_mean_by_year: dict[int, float],
    control_series: list[AnnualSeries],
    project_start_year: int,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    ci: float = DEFAULT_CI,
    seed: int | None = 42,
) -> dict:
    """
    Resamples WHICH control polygons are included (with replacement, same
    pool size each draw) — REAL_DATA_PLAN.md §4.2's exact wording: "a
    bootstrap interval over control polygons". For each resample, averages
    the resampled controls into a control_mean_by_year, computes the
    pre/post effect against the (fixed) treated series, and collects the
    resulting effect-size distribution.

    Returns the point-estimate effect (using ALL controls, not a resample)
    plus the bootstrap distribution's percentile interval.

    seed=42 by default for reproducible demo output (same convention
    precompute_gee.py's compute_placeholder() uses) — pass seed=None for a
    non-reproducible run.
    """
    if not control_series:
        return {
            "effect": None,
            "ci_low": None,
            "ci_high": None,
            "n_bootstrap": n_bootstrap,
            "ci": ci,
            "note": "No control polygons available — cannot compute a DiD effect.",
        }

    def _control_mean_by_year(series_subset: list[AnnualSeries]) -> dict[int, float]:
        years = set()
        for s in series_subset:
            years |= set(s.values_by_year.keys())
        out = {}
        for year in years:
            vals = [s.values_by_year[year] for s in series_subset if year in s.values_by_year]
            if vals:
                out[year] = statistics.mean(vals)
        return out

    point_control_mean = _control_mean_by_year(control_series)
    point_gap = treated_control_gap(treated_mean_by_year, point_control_mean)
    point_result = pre_post_effect(point_gap, project_start_year)
    point_effect = point_result["effect"]

    rng = random.Random(seed)
    n = len(control_series)
    bootstrap_effects: list[float] = []
    for _ in range(n_bootstrap):
        resample = [control_series[rng.randrange(n)] for _ in range(n)]
        cm = _control_mean_by_year(resample)
        gap = treated_control_gap(treated_mean_by_year, cm)
        result = pre_post_effect(gap, project_start_year)
        if result["effect"] is not None:
            bootstrap_effects.append(result["effect"])

    if not bootstrap_effects:
        return {
            "effect": point_effect,
            "ci_low": None,
            "ci_high": None,
            "n_bootstrap": n_bootstrap,
            "ci": ci,
            "n_control_polygons": n,
            "note": "Bootstrap produced no valid resamples (insufficient pre/post year coverage).",
        }

    bootstrap_effects.sort()
    alpha = (1.0 - ci) / 2.0
    lo_idx = int(alpha * len(bootstrap_effects))
    hi_idx = int((1.0 - alpha) * len(bootstrap_effects)) - 1
    hi_idx = max(hi_idx, lo_idx)

    return {
        "effect": point_effect,
        "ci_low": bootstrap_effects[lo_idx],
        "ci_high": bootstrap_effects[hi_idx],
        "n_bootstrap": n_bootstrap,
        "ci": ci,
        "n_control_polygons": n,
        "pre_mean_gap": point_result["pre_mean_gap"],
        "post_mean_gap": point_result["post_mean_gap"],
        "pre_years": point_result["pre_years"],
        "post_years": point_result["post_years"],
    }


def dry_season_windows(start_year: int, end_year: int) -> list[dict]:
    """
    REAL_DATA_PLAN.md §4.2: "Annual dry-season (Nov-Feb) median NDVI and
    MNDWI per polygon, 2016->2026." A "year" Y's dry season runs
    Nov 1 (Y) -> Feb 28/29 (Y+1) — labelled by Y (the November it starts in),
    matching config.py's existing BASELINE/LATEST season-window convention
    used elsewhere in this repo (Nov 1 -> Feb 28/29).
    """
    windows = []
    for year in range(start_year, end_year + 1):
        feb_end_year = year + 1
        is_leap = feb_end_year % 4 == 0 and (feb_end_year % 100 != 0 or feb_end_year % 400 == 0)
        feb_end_day = 29 if is_leap else 28
        windows.append(
            {
                "year": year,
                "start": f"{year}-11-01",
                "end": f"{feb_end_year}-02-{feb_end_day:02d}",
            }
        )
    return windows
