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
