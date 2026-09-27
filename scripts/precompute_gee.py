"""
FR3.1 — treated-vs-control NDVI/MNDWI/NDMI difference-in-differences per
asset, per PRD §12.3 and PLAYBOOK §8.2. Run OFFLINE ONLY.

CLAUDE.md non-negotiable (precompute-first): this script is never imported
by /api or /web. It writes `satellite_results.json`; backend-engineer's
`POST /assets/{id}/satellite` reads and persists it — the live API never
calls Earth Engine.

Usage:
    python scripts/precompute_gee.py [--assets PATH] [--boundary PATH]

Input resolution order if --assets/--boundary aren't given:
    1. backend-engineer's conventional seed output (api/seed/field_records.json
       + api/seed/mws_boundary.geojson) — not confirmed to exist yet as of
       this run; reconcile the exact path at Sync Point 1 if it differs.
    2. Self-generated placeholder boundary + Shapely random-point-in-polygon
       assets (placeholder_data.py), per this agent's role brief.

Credential handling: if gee_client.is_gee_available() is False, this script
does NOT fabricate realistic-looking satellite numbers. It writes results
with "placeholder": true and "source": "synthetic_no_gee_credentials" at
the top level of every record, using a reproducible (record_id-seeded)
pseudo-random generator — never presented as computed evidence
(CLAUDE.md: "never fabricate a number").
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
import placeholder_data
from satellite_scoring import compute_satellite_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_inputs(assets_path: str | None, boundary_path: str | None):
    """Returns (boundary_dict, assets_list, self_generated: bool)."""
    if assets_path and boundary_path:
        return (
            json.loads(Path(boundary_path).read_text()),
            json.loads(Path(assets_path).read_text()),
            False,
        )

    if config.BACKEND_SEED_ASSETS_PATH.exists() and config.BACKEND_SEED_BOUNDARY_PATH.exists():
        logger.info("Using backend-engineer's seed data at %s", config.BACKEND_SEED_ASSETS_PATH.parent)
        return (
            json.loads(config.BACKEND_SEED_BOUNDARY_PATH.read_text()),
            json.loads(config.BACKEND_SEED_ASSETS_PATH.read_text()),
            False,
        )

    logger.warning(
        "No real seed data found (checked %s) — self-generating placeholder "
        "boundary + assets per role brief.",
        config.BACKEND_SEED_ASSETS_PATH.parent,
    )
    boundary_path_out, assets_path_out = placeholder_data.write_placeholder_inputs()
    return (
        json.loads(boundary_path_out.read_text()),
        json.loads(assets_path_out.read_text()),
        True,
    )


def compute_real(asset: dict, other_points: list[tuple[float, float]]) -> dict:
    """
    Real GEE compute path — only reached when gee_client.is_gee_available().
    UNTESTED in this session (see gee_client.py's module docstring) — must
    be validated against a live ee.Initialize() before trusting its output.
    """
    treated, control = gee_client.build_zones(asset["lon"], asset["lat"], other_points)

    tb = gee_client.zone_stats(treated, config.BASELINE_START, config.BASELINE_END)
    ta = gee_client.zone_stats(treated, config.LATEST_START, config.LATEST_END)
    cb = gee_client.zone_stats(control, config.BASELINE_START, config.BASELINE_END)
    ca = gee_client.zone_stats(control, config.LATEST_START, config.LATEST_END)

    did = {}
    for key in ("NDVI", "MNDWI", "NDMI"):
        did[key] = (ta["indices"].get(key, 0.0) - tb["indices"].get(key, 0.0)) - (
            ca["indices"].get(key, 0.0) - cb["indices"].get(key, 0.0)
        )

    # Water-pixel fraction only matters for PT/NC/SM — compute it always
    # anyway since it's cheap relative to the composite build, and it's
    # useful context on the asset drawer chart regardless of category.
    wf_tb = gee_client.water_fraction(treated, config.BASELINE_START, config.BASELINE_END)
    wf_ta = gee_client.water_fraction(treated, config.LATEST_START, config.LATEST_END)
    wf_cb = gee_client.water_fraction(control, config.BASELINE_START, config.BASELINE_END)
    wf_ca = gee_client.water_fraction(control, config.LATEST_START, config.LATEST_END)
    did["water_fraction"] = (wf_ta - wf_tb) - (wf_ca - wf_cb)

    clear_counts = {
        "treated": min(tb["clear_obs_count"], ta["clear_obs_count"]),
        "control": min(cb["clear_obs_count"], ca["clear_obs_count"]),
    }
    # Approximate cloud-confidence signal — a true 0-1 valid-pixel fraction
    # needs dividing by the collection's total candidate-image count for the
    # window, deferred until this path is actually exercised against real
    # data (see gee_client.zone_stats docstring).
    low_confidence = min(clear_counts.values()) < 3

    rain_baseline = gee_client.seasonal_rainfall(treated, config.BASELINE_START, config.BASELINE_END)
    rain_latest = gee_client.seasonal_rainfall(treated, config.LATEST_START, config.LATEST_END)
    pct_change = ((rain_latest - rain_baseline) / rain_baseline * 100) if rain_baseline else None

    return {
        "indices": {
            "treated_before": {**tb["indices"], "water_fraction": wf_tb},
            "treated_after": {**ta["indices"], "water_fraction": wf_ta},
            "control_before": {**cb["indices"], "water_fraction": wf_cb},
            "control_after": {**ca["indices"], "water_fraction": wf_ca},
        },
        "did": did,
        "rainfall": {"baseline_mm": rain_baseline, "latest_mm": rain_latest, "pct_change": pct_change},
        "data_source": {"optical": "LANDSAT/LC08+LC09 C02 T1_L2", "sar_fallback_used": False},
        "valid_pixel_fraction": clear_counts,
        "low_confidence": low_confidence,
        "placeholder": False,
    }


def compute_placeholder(asset: dict) -> dict:
    """
    Reproducible pseudo-random stand-in, clearly flagged, NEVER presented as
    real satellite evidence (CLAUDE.md: never fabricate a number). Seeded on
    record_id so reruns are stable for demo purposes — deliberately noisy,
    not tuned to "look good."
    """
    rng = random.Random(f"sat-placeholder-{asset['record_id']}")
    did = {
        "NDVI": round(rng.uniform(-0.05, 0.12), 4),
        "MNDWI": round(rng.uniform(-0.03, 0.07), 4),
        "NDMI": round(rng.uniform(-0.05, 0.10), 4),
        "water_fraction": round(rng.uniform(-0.05, 0.25), 4),
    }
    zeros = {"NDVI": 0.0, "MNDWI": 0.0, "NDMI": 0.0, "water_fraction": 0.0}
    return {
        "indices": {
            "treated_before": zeros, "treated_after": zeros,
            "control_before": zeros, "control_after": zeros,
        },
        "did": did,
        "rainfall": {"baseline_mm": None, "latest_mm": None, "pct_change": None},
        "data_source": {"optical": None, "sar_fallback_used": False},
        "valid_pixel_fraction": {"treated": None, "control": None},
        "low_confidence": False,
        "placeholder": True,
        "source": "synthetic_no_gee_credentials",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="FR3.1 satellite DiD precompute (offline only)")
    parser.add_argument("--assets", help="Path to asset points JSON (record_id/lat/lon/category)")
    parser.add_argument("--boundary", help="Path to MWS boundary GeoJSON")
    args = parser.parse_args()

    boundary, assets, self_generated = load_inputs(args.assets, args.boundary)

    gee_ok, gee_reason = gee_client.is_gee_available()
    if gee_ok:
        logger.info("Earth Engine available — running real compute.")
    else:
        logger.warning(
            "Earth Engine NOT available (%s) — writing placeholder results, "
            "flagged placeholder=true/source=synthetic_no_gee_credentials.",
            gee_reason,
        )

    all_points = [(a["lon"], a["lat"]) for a in assets]
    results = []
    for asset in assets:
        others = [
            (lon, lat) for (lon, lat) in all_points
            if (lon, lat) != (asset["lon"], asset["lat"])
        ]

        if gee_ok:
            sat = compute_real(asset, others)
        else:
            sat = compute_placeholder(asset)

        score_result = compute_satellite_score(asset["category"], sat["did"])

        notes = list(score_result.notes)
        if self_generated:
            notes.append(
                "Boundary/assets are self-generated placeholders, not "
                "backend-engineer's real seed data (Round 1 hadn't landed "
                "as of this run)."
            )

        record = {
            "record_id": asset["record_id"],
            "mws_id": config.MWS_ID,
            "category": asset["category"],
            "baseline_window": [config.BASELINE_START, config.BASELINE_END],
            "latest_window": [config.LATEST_START, config.LATEST_END],
            "treated_buffer_m": config.TREATED_BUFFER_M,
            "control_ring_m": [config.CONTROL_RING_INNER_M, config.CONTROL_RING_OUTER_M],
            **sat,
            "primary_index_for_category": score_result.primary_index_for_category,
            "did_classification": score_result.did_classification.value,
            "satellite_score": score_result.satellite_score,
            "notes": notes,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.SATELLITE_RESULTS_PATH.write_text(json.dumps(results, indent=2))
    logger.info("Wrote %d satellite results to %s", len(results), config.SATELLITE_RESULTS_PATH)


if __name__ == "__main__":
    main()
