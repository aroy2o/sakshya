"""
Central, non-hardcoded configuration for Phase 3 (PRD §10 Phase 3, §14).

CLAUDE.md non-negotiable: "watershed choice is config, not code." Nothing
in the Phase 3 scripts should bury MWS_ID, season windows, or buffer sizes
as inline literals — everything lives here, overridable via env vars, so
swapping the demo watershed (or recalibrating a buffer/season default)
costs zero code changes elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Watershed identity (PRD §14) -------------------------------------------
# Current leading candidate per PRD §14 / AGENTS.md autonomous-run instruction.
MWS_ID = os.environ.get("SAKSHYA_MWS_ID", "4120883730")  # Marigaon HYBAS_ID
MWS_NAME = os.environ.get("SAKSHYA_MWS_NAME", "Marigaon")

# --- Season windows -----------------------------------------------------
# ASSUMPTION (stated explicitly per role brief): Nov 1 - Feb 28/29, both
# years — post-monsoon into winter. Avoids Assam/NE India's Jun-Sep monsoon
# cloud cover, matching CLAUDE.md's "use dry-season median composites for
# cloud cover" instruction. Baseline = a pre-project reference window;
# latest = the most recent complete dry season before today. These belong
# to the mws table's baseline_start/baseline_end/latest_start/latest_end
# columns (PRD §8) — env-var overrides here exist so this script never
# hardcodes them, but the source of truth once the DB exists is that row,
# not this file.
BASELINE_START = os.environ.get("SAKSHYA_BASELINE_START", "2019-11-01")
BASELINE_END = os.environ.get("SAKSHYA_BASELINE_END", "2020-02-29")
LATEST_START = os.environ.get("SAKSHYA_LATEST_START", "2025-11-01")
LATEST_END = os.environ.get("SAKSHYA_LATEST_END", "2026-02-28")

# --- Buffer geometry ------------------------------------------------------
# ASSUMPTION (stated explicitly per role brief): PLAYBOOK §8.2's starter
# values. Treated = 200 m radius. Control = annulus 350 m-1000 m (a 150 m
# gap past the treated edge avoids spatial bleed between the two zones).
# Symmetric across all activity categories in this round — PLAYBOOK's
# suggestion of an asymmetric downstream sector for ponds/check-dams is a
# documented future refinement, out of scope for FR3.1 as written.
TREATED_BUFFER_M = 200
CONTROL_RING_INNER_M = 350
CONTROL_RING_OUTER_M = 1000
# Control zones also exclude every OTHER asset's treated buffer, so one
# site's control ring never overlaps a neighboring site's treated zone.
OTHER_ASSET_EXCLUSION_BUFFER_M = TREATED_BUFFER_M

# --- Cloud-cover fallback -------------------------------------------------
# Below this fraction of valid (non-cloud-masked) observations in a
# zone/window, mark low_confidence=True and (for water-related indices
# only) attempt a Sentinel-1 SAR supplement rather than silently returning
# a noisy optical number (CLAUDE.md: "don't silently return a noisy
# result").
MIN_VALID_PIXEL_FRACTION = 0.6

# --- Output paths ----------------------------------------------------------
SCRIPTS_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPTS_DIR / "output" / MWS_ID
SATELLITE_RESULTS_PATH = OUTPUT_DIR / "satellite_results.json"
THEMATIC_DIR = OUTPUT_DIR / "thematic"
THEMATIC_MANIFEST_PATH = THEMATIC_DIR / "manifest.json"

# Conventional location backend-engineer's Phase 1 seed script is expected
# to write to. Not confirmed yet (Round 1 hadn't landed as of this run) —
# precompute_gee.py checks here first and falls back to self-generated
# placeholder data if absent. Reconcile at Sync Point 1 if the real path
# differs.
BACKEND_SEED_ASSETS_PATH = SCRIPTS_DIR.parent / "api" / "seed" / "field_records.json"
BACKEND_SEED_BOUNDARY_PATH = SCRIPTS_DIR.parent / "api" / "seed" / "mws_boundary.geojson"

# --- Reality Pass R1/R2 (docs/REAL_DATA_PLAN.md) ---------------------------
# Real-data source identity. Overridable via env so "watershed choice is
# config, not code" (CLAUDE.md non-negotiable) still holds for the Reality
# Pass sourcing scripts, not just the original seed pipeline.
REAL_DATA_DIR = SCRIPTS_DIR.parent / "data" / "real"
REAL_DATA_RAW_CACHE_DIR = REAL_DATA_DIR / "raw_cache"

TREATED_DISTRICT_NAME = os.environ.get("SAKSHYA_TREATED_DISTRICT", "Marigaon")  # LGD dtname spelling
TREATED_STATE_NAME = os.environ.get("SAKSHYA_TREATED_STATE", "ASSAM")

# bharatlas.com CC0-1.0 mirrors (REAL_DATA_PLAN.md §2, items 1 and 3).
BHARATLAS_LGD_DISTRICTS_URL = os.environ.get(
    "SAKSHYA_LGD_DISTRICTS_URL",
    "https://bharatlas.com/api/dl/admin/districts/LGD_Districts.parquet",
)
BHARATLAS_SLUSI_MWS_URL = os.environ.get(
    "SAKSHYA_SLUSI_MWS_URL",
    "https://pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/environment/slusi-micro-watersheds/SLUSI_MicroWatersheds.parquet",
)

# ESA WorldCover v200 (2021), 10 m, public AWS Open Data bucket, no auth.
# Cloud-Optimized GeoTIFF, 3x3 degree tiles named by SW corner
# (verified this session: prefix listing returned exactly one match).
ESA_WORLDCOVER_S3_TEMPLATE = os.environ.get(
    "SAKSHYA_ESA_WORLDCOVER_S3_TEMPLATE",
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif",
)
# WorldCover class codes (ESA WorldCover v200 product legend).
WORLDCOVER_CROP_CLASS = 40
WORLDCOVER_BUILTUP_CLASS = 50
WORLDCOVER_WATER_CLASS = 80
WORLDCOVER_WETLAND_CLASS = 90
WORLDCOVER_TREE_CLASS = 10

# Copernicus DEM GLO-30, 30 m, public AWS Open Data bucket, no auth.
# Cloud-Optimized GeoTIFF, 1x1 degree tiles (verified this session). `tile`
# must already be in the bucket's own "N26_00_E092_00" form (see
# _dem_tiles_for_bbox in fetch_real_boundaries.py) — NOT plain "N26E092".
COPERNICUS_DEM_S3_TEMPLATE = os.environ.get(
    "SAKSHYA_COPERNICUS_DEM_S3_TEMPLATE",
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{tile}_DEM/Copernicus_DSM_COG_10_{tile}_DEM.tif",
)

# UTM zone for Assam — used for area-accurate (not degree-squared) polygon
# area computation. EPSG:32646 = WGS84 / UTM zone 46N, correct for
# Marigaon/Assam's ~92E longitude.
LOCAL_PROJECTED_CRS = os.environ.get("SAKSHYA_LOCAL_CRS", "EPSG:32646")

# How many top-ranked, non-excluded candidate micro-watersheds become the
# demo's "treated" boundary when no human-supplied config/treated_mws.txt
# exists (REAL_DATA_PLAN.md §9 item 2 is still an open human step as of
# this run). See candidate_ranking.py for the scoring/exclusion logic.
TOP_K_TREATED = int(os.environ.get("SAKSHYA_TOP_K_TREATED", "5"))

# --- R2 watershed-level time series (REAL_DATA_PLAN.md §4.2) ---------------
# Annual dry-season (Nov-Feb) windows, 2016 -> most recent COMPLETE dry
# season before today (2026-09-28 at the time this was set — dry season
# "2025" runs Nov 2025 -> Feb 2026, already finished). Real WDC-1 project
# start = 2021-22 per REAL_DATA_PLAN.md §1's `MARIGAON-WDC - 1 /2021-22`.
TIMESERIES_START_YEAR = int(os.environ.get("SAKSHYA_TIMESERIES_START_YEAR", "2016"))
TIMESERIES_END_YEAR = int(os.environ.get("SAKSHYA_TIMESERIES_END_YEAR", "2025"))
PROJECT_START_YEAR = int(os.environ.get("SAKSHYA_PROJECT_START_YEAR", "2021"))

WATERSHED_TIMESERIES_PATH = OUTPUT_DIR / "watershed_timeseries.json"
WATERSHED_DID_SUMMARY_PATH = OUTPUT_DIR / "watershed_did_summary.json"
