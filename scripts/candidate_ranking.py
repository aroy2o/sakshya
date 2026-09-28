"""
R1 (docs/REAL_DATA_PLAN.md §1, §2 items 1-3, §8's R1 row; also feeds R2's
matched-control design, §4.1) — automated treated/control micro-watershed
candidate ranking.

Used ONLY as a fallback when no human has supplied `config/treated_mws.txt`
(REAL_DATA_PLAN.md §9 item 2 — confirming the real MARIGAON-WDC-1/2021-22
project's actual micro-watershed codes via the Srishti/Tejas Bharat map is
an explicit human-only step, not yet done as of this run). Every metric fed
into this module is computed from real, sourced land-cover/elevation data
(ESA WorldCover v200, Copernicus DEM GLO-30 — see fetch_real_boundaries.py
for the I/O side that produces these numbers). This module itself is pure:
given already-computed per-candidate metrics, it filters, scores, ranks,
and does control-matching. No network, fully unit-testable — same
separation-of-concerns pattern as satellite_scoring.py (pure) vs.
precompute_gee.py (I/O) elsewhere in this repo.

IMPORTANT — labelling requirement: this is an AUTOMATED PICK, not a
confirmed mapping to the real project's actual micro-watersheds. Every
output must carry `pick_method="automated_ranking_pending_human_confirmation"`
end to end so the API/UI never presents this as ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PICK_METHOD_AUTOMATED = "automated_ranking_pending_human_confirmation"
PICK_METHOD_HUMAN_CONFIRMED = "human_confirmed_config_treated_mws_txt"
PICK_METHOD = PICK_METHOD_AUTOMATED  # backward-compatible alias — most callers only need the automated case

# --- Exclusion thresholds ---------------------------------------------------
# PROVISIONAL — PRD/PLAYBOOK give no numeric cutoff for any of these
# (same treatment satellite_scoring.THRESHOLDS gives its own constants:
# a documented hackathon-stage starting point, flagged for calibration).
MAX_BUILT_UP_SHARE = 0.15  # exclude candidates >15% built-up — not a plausible NRM watershed-works site
MAX_WATER_SHARE = 0.30  # exclude candidates >30% permanent water — REAL_DATA_PLAN.md §4.3's
# Brahmaputra-floodplain confounder warning: prefer polygons away from the main channel.
MIN_AREA_HA = 50.0  # exclude slivers (SLUSI micro-watersheds are documented ~500-5000 ha typical, REAL_DATA_PLAN.md §1)
MAX_AREA_HA = 8000.0  # exclude anomalously large merged/dissolved polygons

# --- Composite score weights (provisional; sum to 1.0) ---------------------
# Crop share is the strongest available proxy for "agricultural land where
# NRM watershed works are typically sited" given REAL_DATA_PLAN.md §1's
# activity mix (~21 farm ponds, ~21 contour bunds, 2 check dams, 2 Amrit
# Sarovar in the real project). Built-up and water are penalised as proxies
# for "not agricultural / not a stable satellite signal".
WEIGHT_CROP_SHARE = 0.5
WEIGHT_LOW_BUILT_UP = 0.3
WEIGHT_LOW_WATER = 0.2

# Slope band informally preferred for NRM watershed works (contour
# bunds/check dams need *some* relief to be meaningful; dead-flat
# floodplain has no gradient for a bund to hold; very steep terrain is
# erosion-prone / atypical for farm ponds). PRD/PLAYBOOK give no numeric
# slope target — this is a documented, provisional domain heuristic,
# reported per-candidate for context but deliberately NOT folded into
# composite_score (so a wrong guess here can't silently dominate ranking).
SLOPE_PREFERRED_MIN_DEG = 1.0
SLOPE_PREFERRED_MAX_DEG = 8.0

# --- Matched-control criteria -----------------------------------------------
# REAL_DATA_PLAN.md §4.1, verbatim: "Controls = neighbouring micro-watersheds
# with no WDC project, matched on baseline dry-season NDVI (±10%), crop
# share (±15%) and slope, excluding polygons with high built-up or
# permanent-water share."
CONTROL_CROP_SHARE_TOLERANCE = 0.15  # ±15% relative, per §4.1
CONTROL_SLOPE_TOLERANCE_DEG = 3.0  # absolute degrees — no PRD/plan source; provisional
CONTROL_NDVI_TOLERANCE = 0.10  # ±10% relative, per §4.1 — NOT APPLIED here, see match_controls()


@dataclass
class CandidateMetrics:
    """Per-candidate real, sourced metrics (computed by fetch_real_boundaries.py
    from ESA WorldCover + Copernicus DEM — never fabricated)."""

    id: str
    mws_code: str | None
    district: str | None
    area_ha: float
    crop_share: float
    built_up_share: float
    water_share: float
    tree_share: float
    mean_slope_deg: float | None
    pixel_count: int = 0  # candidates with 0 valid land-cover pixels (e.g. entirely outside raster coverage) are always excluded


@dataclass
class RankedCandidate(CandidateMetrics):
    composite_score: float = 0.0
    excluded: bool = False
    exclusion_reason: str | None = None
    rank: int | None = None


def passes_exclusion(m: CandidateMetrics) -> tuple[bool, str | None]:
    """PRD/plan gives no numeric cutoffs — these are this module's own
    documented, provisional thresholds (see module docstring)."""
    if m.pixel_count <= 0:
        return False, "no valid land-cover pixels (outside fetched raster coverage)"
    if m.area_ha < MIN_AREA_HA:
        return False, f"area_ha {m.area_ha:.1f} < MIN_AREA_HA {MIN_AREA_HA}"
    if m.area_ha > MAX_AREA_HA:
        return False, f"area_ha {m.area_ha:.1f} > MAX_AREA_HA {MAX_AREA_HA}"
    if m.built_up_share > MAX_BUILT_UP_SHARE:
        return False, f"built_up_share {m.built_up_share:.3f} > MAX_BUILT_UP_SHARE {MAX_BUILT_UP_SHARE}"
    if m.water_share > MAX_WATER_SHARE:
        return False, f"water_share {m.water_share:.3f} > MAX_WATER_SHARE {MAX_WATER_SHARE}"
    return True, None


def composite_score(m: CandidateMetrics) -> float:
    """Higher is better. See module docstring for weight rationale."""
    return (
        WEIGHT_CROP_SHARE * m.crop_share
        + WEIGHT_LOW_BUILT_UP * (1.0 - m.built_up_share)
        + WEIGHT_LOW_WATER * (1.0 - m.water_share)
    )


def in_preferred_slope_band(slope_deg: float | None) -> bool | None:
    """Reporting-only signal (see SLOPE_PREFERRED_* docstring above) —
    returns None (unknown) when slope wasn't computed for this candidate."""
    if slope_deg is None:
        return None
    return SLOPE_PREFERRED_MIN_DEG <= slope_deg <= SLOPE_PREFERRED_MAX_DEG


def rank_candidates(candidates: list[CandidateMetrics]) -> list[RankedCandidate]:
    """Scores every candidate, applies exclusion rules, and ranks the
    eligible (non-excluded) ones by composite_score descending. Excluded
    candidates keep composite_score for transparency but rank=None."""
    ranked: list[RankedCandidate] = []
    for m in candidates:
        ok, reason = passes_exclusion(m)
        score = composite_score(m)
        ranked.append(
            RankedCandidate(
                id=m.id,
                mws_code=m.mws_code,
                district=m.district,
                area_ha=m.area_ha,
                crop_share=m.crop_share,
                built_up_share=m.built_up_share,
                water_share=m.water_share,
                tree_share=m.tree_share,
                mean_slope_deg=m.mean_slope_deg,
                pixel_count=m.pixel_count,
                composite_score=score,
                excluded=not ok,
                exclusion_reason=reason,
                rank=None,
            )
        )

    eligible = [r for r in ranked if not r.excluded]
    eligible.sort(key=lambda r: r.composite_score, reverse=True)
    for i, r in enumerate(eligible, start=1):
        r.rank = i
    return ranked


def select_treated(ranked: list[RankedCandidate], top_k: int) -> list[RankedCandidate]:
    """Top-K eligible candidates by rank. This is the automated stand-in for
    a human-confirmed config/treated_mws.txt — callers MUST label output
    with PICK_METHOD."""
    eligible = [r for r in ranked if not r.excluded and r.rank is not None]
    eligible.sort(key=lambda r: r.rank)
    return eligible[:top_k]


def match_controls(
    treated: list[CandidateMetrics],
    pool: list[RankedCandidate],
    treated_ids: set[str],
) -> list[dict]:
    """
    REAL_DATA_PLAN.md §4.1 matched-control selection. For the treated set's
    mean crop_share/slope, finds pool candidates (excluding anything in
    `treated_ids`; pool entries must already be non-excluded — built-up/
    water-share exclusion is applied upstream by rank_candidates) within
    tolerance on crop share and slope.

    NDVI matching (§4.1's third criterion, ±10%) is NOT applied here — it
    needs a live GEE dry-season NDVI composite, which is blocked as of this
    run (PROGRESS.md "Needs your attention": IAM permission error, human
    action required). Every returned match carries `"ndvi_match":
    "pending_gee"` so nothing downstream mistakes this for the full §4.1
    three-criteria match — once GEE is live, re-run with NDVI values filled
    in and this function should be extended to actually filter on it.
    """
    if not treated:
        return []

    treated_crop_mean = sum(t.crop_share for t in treated) / len(treated)
    treated_slope_vals = [t.mean_slope_deg for t in treated if t.mean_slope_deg is not None]
    treated_slope_mean = sum(treated_slope_vals) / len(treated_slope_vals) if treated_slope_vals else None

    matches: list[dict] = []
    for c in pool:
        if c.id in treated_ids or c.excluded:
            continue

        crop_ok = (
            treated_crop_mean > 0
            and abs(c.crop_share - treated_crop_mean) / treated_crop_mean <= CONTROL_CROP_SHARE_TOLERANCE
        )
        if treated_slope_mean is None or c.mean_slope_deg is None:
            slope_ok = True  # can't evaluate — don't let missing slope silently exclude every candidate
            slope_evaluated = False
        else:
            slope_ok = abs(c.mean_slope_deg - treated_slope_mean) <= CONTROL_SLOPE_TOLERANCE_DEG
            slope_evaluated = True

        if crop_ok and slope_ok:
            matches.append(
                {
                    "id": c.id,
                    "mws_code": c.mws_code,
                    "district": c.district,
                    "crop_share": c.crop_share,
                    "built_up_share": c.built_up_share,
                    "water_share": c.water_share,
                    "mean_slope_deg": c.mean_slope_deg,
                    "crop_share_match": crop_ok,
                    "slope_match": slope_ok if slope_evaluated else "not_evaluated_missing_slope",
                    "ndvi_match": "pending_gee",
                }
            )
    return matches
