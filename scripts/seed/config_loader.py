"""Loads the demo watershed config — PRD §14 / CLAUDE.md "watershed choice is
config, not code". Never hardcode a watershed id/boundary anywhere else;
read it through this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # scripts/seed/ -> scripts/ -> repo root

DEFAULT_CONFIG_PATH = "scripts/config/watershed.yaml"


@dataclass
class WatershedConfig:
    id: str
    name: str | None
    project_id: str | None
    state: str | None
    district: str | None
    boundary_path: Path
    is_synthetic_boundary: bool
    baseline_start: str
    baseline_end: str
    latest_start: str
    latest_end: str


def load_watershed_config(config_path: str | None = None) -> WatershedConfig:
    """Reads the path from SEED_WATERSHED_CONFIG env var if not given explicitly,
    falling back to DEFAULT_CONFIG_PATH — this is the one place the watershed
    choice is resolved from config rather than hardcoded."""
    path_str = config_path or os.environ.get("SEED_WATERSHED_CONFIG", DEFAULT_CONFIG_PATH)
    path = Path(path_str)
    if not path.is_absolute():
        path = REPO_ROOT / path
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    boundary_path = Path(raw["boundary_path"])
    if not boundary_path.is_absolute():
        boundary_path = REPO_ROOT / boundary_path

    return WatershedConfig(
        id=str(raw["id"]),
        name=raw.get("name"),
        project_id=raw.get("project_id"),
        state=raw.get("state"),
        district=raw.get("district"),
        boundary_path=boundary_path,
        is_synthetic_boundary=bool(raw.get("is_synthetic_boundary", True)),
        baseline_start=raw["baseline_start"],
        baseline_end=raw["baseline_end"],
        latest_start=raw["latest_start"],
        latest_end=raw["latest_end"],
    )
