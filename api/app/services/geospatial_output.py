"""Read-only access to geospatial-engineer's precomputed Phase 3 output
(scripts/output/{mws_id}/...) — FR3.3 / FR3.4.

This module never computes anything and never calls Earth Engine: it only
reads files geospatial-engineer's offline `scripts/precompute_gee.py` already
wrote to disk (precompute-first non-negotiable, CLAUDE.md). If the expected
file is missing, that's surfaced as a clear 404 by the caller, never
silently faked (CLAUDE.md "never fabricate a number").
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings

# The 6 layer keys PRD §9 exposes via GET /mws/{id}/thematic/{layer}.
# `slope` lives under the manifest's "supporting_artifacts" key and is
# deliberately NOT included here — coordinator ruling at Sync Point 1:
# Phase 5's FR5.1 doesn't need it as a toggleable layer (kept for the
# Phase 6 report card instead).
THEMATIC_LAYERS: tuple[str, ...] = (
    "drainage",
    "lulc",
    "ndvi_before",
    "ndvi_after",
    "ndvi_change",
    "water",
)


def output_root() -> Path:
    return Path(get_settings().geospatial_output_dir)


def mws_dir(mws_id: str) -> Path:
    return output_root() / mws_id


def thematic_dir(mws_id: str) -> Path:
    return mws_dir(mws_id) / "thematic"


def load_thematic_manifest(mws_id: str) -> dict:
    """Raises FileNotFoundError if geospatial-engineer hasn't precomputed
    this mws yet - caller turns that into a 404."""
    path = thematic_dir(mws_id) / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_thematic_geojson(mws_id: str, relative_path: str) -> dict:
    path = thematic_dir(mws_id) / relative_path
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_satellite_results(mws_id: str) -> list[dict]:
    """Raises FileNotFoundError if this mws has no precomputed satellite
    results yet - caller turns that into a 404."""
    path = mws_dir(mws_id) / "satellite_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
