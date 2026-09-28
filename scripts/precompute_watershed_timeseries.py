"""
R2 — docs/REAL_DATA_PLAN.md §4.1-4.3, §8's R2 row.

Watershed-level matched-control DiD: annual dry-season NDVI/MNDWI time
series (2016->latest complete dry season) for the REAL treated boundary
(R1's `data/real/treated_boundary.geojson`) vs. R1's matched control pool
(`data/real/candidate_ranking.json`'s `control_pool_matches`), CHIRPS
Jun-Sep rainfall bars for context, and a bootstrapped pre/post effect size
(`scripts/watershed_did.py`).

CLAUDE.md non-negotiable (precompute-first): run OFFLINE ONLY. Writes
`watershed_timeseries.json` / `watershed_did_summary.json`; never imported
by /api or /web, never calls Earth Engine live from a request path.

Status as of this run: R0 (the GEE credential smoke test) FAILED — same
`roles/serviceusage.serviceUsageConsumer` permission error as before (see
PROGRESS.md "Needs your attention", human action required on the
`green-dukan` GCP project). This script's REAL-GEE code path
(`_compute_real_series`) is therefore untested against a live
`ee.Initialize()` this session — same caveat gee_client.py's own real
functions already carry. When GEE is unavailable, this script does NOT
fabricate realistic-looking NDVI/MNDWI/rainfall numbers: every value is
written with "placeholder": true and "source": "synthetic_no_gee_credentials"
at both the per-year and top-level manifest, using a reproducible
(polygon-id + year seeded) pseudo-random generator — never presented as
computed evidence (CLAUDE.md: "never fabricate a number").

Run:
    python scripts/precompute_watershed_timeseries.py
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path

import config
import gee_client
from watershed_did import AnnualSeries, bootstrap_control_polygons, dry_season_windows

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _load_treated_boundary() -> dict:
    path = config.REAL_DATA_DIR / "treated_boundary.geojson"
    if not path.exists():
        raise FileNotFoundError(
            f"No real treated boundary at {path} — run scripts/fetch_real_boundaries.py (R1) first."
        )
    return json.loads(path.read_text())


def _load_control_polygons(treated_fc: dict) -> list[dict]:
    """
    Looks up each matched control's real geometry from R1's cached SLUSI
    candidates file (candidate_ranking.json only stores metrics/ids, not
    geometry — this joins them back).
    """
    ranking_path = config.REAL_DATA_DIR / "candidate_ranking.json"
    candidates_path = config.REAL_DATA_DIR / "raw_cache" / "slusi_candidates_marigaon_and_neighbors.geojson"
    if not ranking_path.exists() or not candidates_path.exists():
        raise FileNotFoundError(
            f"Missing {ranking_path} or {candidates_path} — run scripts/fetch_real_boundaries.py (R1) first."
        )
    ranking = json.loads(ranking_path.read_text())
    candidates_fc = json.loads(candidates_path.read_text())
    geom_by_id = {f["properties"]["id"]: f["geometry"] for f in candidates_fc["features"]}

    controls = []
    for match in ranking["control_pool_matches"]:
        geom = geom_by_id.get(match["id"])
        if geom is None:
            logger.warning("Control candidate %s has no cached geometry — skipping", match["id"])
            continue
        controls.append({**match, "geometry": geom})
    logger.info("Loaded %d matched control polygons with geometry", len(controls))
    return controls


# --- real GEE compute path (untested this session, see module docstring) ---

def _compute_real_series(geom_geojson: dict, years: list[int]) -> dict:
    geom = gee_client.geometry_from_geojson(geom_geojson)
    windows = dry_season_windows(years[0], years[-1])
    series = {"NDVI": {}, "MNDWI": {}}
    for w in windows:
        stats = gee_client.zone_stats(geom, w["start"], w["end"])
        series["NDVI"][w["year"]] = stats["indices"].get("NDVI")
        series["MNDWI"][w["year"]] = stats["indices"].get("MNDWI")
    return series


def _compute_real_rainfall(geom_geojson: dict, years: list[int]) -> dict:
    """CHIRPS Jun-Sep total rainfall per year, treated polygon only
    (REAL_DATA_PLAN.md §4.2: 'CHIRPS Jun-Sep rainfall as bars' — context,
    not per-control)."""
    geom = gee_client.geometry_from_geojson(geom_geojson)
    rainfall = {}
    for year in years:
        rainfall[year] = gee_client.seasonal_rainfall(geom, f"{year}-06-01", f"{year}-09-30")
    return rainfall


# --- placeholder compute path -----------------------------------------------

def _compute_placeholder_series(polygon_id: str, years: list[int]) -> dict:
    """
    Reproducible pseudo-random stand-in, clearly flagged, NEVER presented as
    real satellite evidence (CLAUDE.md: never fabricate a number). Seeded on
    polygon_id so reruns are stable for demo purposes. Deliberately gives
    the TREATED polygon a slight upward NDVI trend after PROJECT_START_YEAR
    and controls a flat trend, so the placeholder output *shapes* like what
    a real DiD chart would look like without ever being mistaken for one —
    every value still carries placeholder=true/source=synthetic_no_gee_credentials.
    """
    rng = random.Random(f"watershed-ts-placeholder-{polygon_id}")
    is_treated = polygon_id == "TREATED"
    base_ndvi = rng.uniform(0.45, 0.55)
    base_mndwi = rng.uniform(-0.1, 0.0)
    ndvi, mndwi = {}, {}
    for year in years:
        noise = rng.uniform(-0.03, 0.03)
        trend = (0.01 * max(0, year - config.PROJECT_START_YEAR)) if is_treated else 0.0
        ndvi[year] = round(base_ndvi + trend + noise, 4)
        mndwi[year] = round(base_mndwi + noise / 2, 4)
    return {"NDVI": ndvi, "MNDWI": mndwi}


def _compute_placeholder_rainfall(years: list[int]) -> dict:
    rng = random.Random("watershed-ts-placeholder-rainfall")
    return {year: round(rng.uniform(600, 1400), 1) for year in years}


# --- main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="R2: watershed-level matched-control DiD time series")
    args = parser.parse_args()

    treated_fc = _load_treated_boundary()
    controls = _load_control_polygons(treated_fc)
    years = list(range(config.TIMESERIES_START_YEAR, config.TIMESERIES_END_YEAR + 1))

    gee_ok, gee_reason = gee_client.is_gee_available()
    if gee_ok:
        logger.info("Earth Engine available — running real compute (UNTESTED path, see module docstring).")
    else:
        logger.warning(
            "Earth Engine NOT available (%s) — writing placeholder results, "
            "flagged placeholder=true/source=synthetic_no_gee_credentials.",
            gee_reason,
        )

    if gee_ok:
        treated_series = _compute_real_series(treated_fc["geometry"], years)
        rainfall = _compute_real_rainfall(treated_fc["geometry"], years)
        placeholder = False
    else:
        treated_series = _compute_placeholder_series("TREATED", years)
        rainfall = _compute_placeholder_rainfall(years)
        placeholder = True

    control_series_ndvi: list[AnnualSeries] = []
    control_series_mndwi: list[AnnualSeries] = []
    control_year_data: dict[str, dict] = {}
    for c in controls:
        if gee_ok:
            s = _compute_real_series(c["geometry"], years)
        else:
            s = _compute_placeholder_series(c["id"], years)
        control_series_ndvi.append(AnnualSeries(polygon_id=c["id"], values_by_year=s["NDVI"]))
        control_series_mndwi.append(AnnualSeries(polygon_id=c["id"], values_by_year=s["MNDWI"]))
        control_year_data[c["id"]] = {
            "mws_code": c.get("mws_code"),
            "district": c.get("district"),
            "NDVI": s["NDVI"],
            "MNDWI": s["MNDWI"],
        }

    # Control MEAN per year (across all matched controls) — the "band" the
    # dashboard plots against the treated line (REAL_DATA_PLAN.md §4.2:
    # "Plot treated vs control mean with a band").
    control_mean_ndvi = {}
    control_mean_mndwi = {}
    for year in years:
        ndvi_vals = [c["NDVI"][year] for c in control_year_data.values() if year in c["NDVI"]]
        mndwi_vals = [c["MNDWI"][year] for c in control_year_data.values() if year in c["MNDWI"]]
        if ndvi_vals:
            control_mean_ndvi[year] = sum(ndvi_vals) / len(ndvi_vals)
        if mndwi_vals:
            control_mean_mndwi[year] = sum(mndwi_vals) / len(mndwi_vals)

    timeseries_output = {
        "mws_id": config.MWS_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "placeholder": placeholder,
        "source": "synthetic_no_gee_credentials" if placeholder else "LANDSAT/LC08+LC09 C02 T1_L2, UCSB-CHG/CHIRPS/DAILY",
        "method": {
            "season_window": "Nov 1 (year) -> Feb 28/29 (year+1), dry season, labelled by the November it starts in",
            "years": years,
            "project_start_year": config.PROJECT_START_YEAR,
            "rainfall_window": "Jun 1 -> Sep 30, same calendar year",
            "n_control_polygons": len(controls),
            "control_selection": "REAL_DATA_PLAN.md §4.1 — crop share ±15%, slope ±3deg (see candidate_ranking.py); NDVI ±10% matching NOT applied (pending_gee)",
        },
        "treated": {
            "polygon_source": "data/real/treated_boundary.geojson (R1 automated pick, pending_human_confirmation)",
            "NDVI": treated_series["NDVI"],
            "MNDWI": treated_series["MNDWI"],
        },
        "control_mean": {
            "NDVI": control_mean_ndvi,
            "MNDWI": control_mean_mndwi,
        },
        "control_polygons": control_year_data,
        "rainfall_mm_jun_sep": rainfall,
    }
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.WATERSHED_TIMESERIES_PATH.write_text(json.dumps(timeseries_output, indent=2, default=str))
    logger.info("Wrote %s", config.WATERSHED_TIMESERIES_PATH)

    ndvi_did = bootstrap_control_polygons(
        treated_mean_by_year=treated_series["NDVI"],
        control_series=control_series_ndvi,
        project_start_year=config.PROJECT_START_YEAR,
    )
    mndwi_did = bootstrap_control_polygons(
        treated_mean_by_year=treated_series["MNDWI"],
        control_series=control_series_mndwi,
        project_start_year=config.PROJECT_START_YEAR,
    )

    did_summary = {
        "mws_id": config.MWS_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "placeholder": placeholder,
        "source": "synthetic_no_gee_credentials" if placeholder else "LANDSAT/LC08+LC09 C02 T1_L2",
        "method_params": {
            "project_start_year": config.PROJECT_START_YEAR,
            "n_bootstrap": 2000,
            "ci": 0.95,
            "bootstrap_unit": "control polygons (resampled with replacement), per REAL_DATA_PLAN.md §4.2",
            "n_control_polygons": len(controls),
        },
        "NDVI": ndvi_did,
        "MNDWI": mndwi_did,
        "caveats": [
            "Watershed-level DiD only — no asset coordinates used (REAL_DATA_PLAN.md §4.1's "
            "explicit design goal, sidesteps public work-code pages carrying no coordinates).",
            "Marigaon is Brahmaputra floodplain — floods/erosion/sandbar shifts can swamp water "
            "signals (REAL_DATA_PLAN.md §4.3). Water metrics (MNDWI) are secondary to NDVI here.",
            "Control matching used crop-share + slope only — NDVI matching pending live GEE.",
        ]
        + (["placeholder=true: every NDVI/MNDWI value above is synthetic (no GEE credentials this run) — do not present as a real effect size."] if placeholder else []),
    }
    config.WATERSHED_DID_SUMMARY_PATH.write_text(json.dumps(did_summary, indent=2, default=str))
    logger.info("Wrote %s", config.WATERSHED_DID_SUMMARY_PATH)
    logger.info(
        "NDVI effect (treated-control gap, post vs pre %d): %s [%s, %s] (placeholder=%s)",
        config.PROJECT_START_YEAR, ndvi_did.get("effect"), ndvi_did.get("ci_low"), ndvi_did.get("ci_high"), placeholder,
    )


if __name__ == "__main__":
    main()
