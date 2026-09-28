"""Read-only access to R3's precomputed WDC-PMKSY registry output
(scripts/output/registry/, written by scripts/fetch_gt2.py).

Precompute-first, same pattern as app/services/geospatial_output.py: this
module never fetches wdcpmksy.dolr.gov.in or parses HTML itself, it only
reads what scripts/fetch_gt2.py already wrote to disk (CLAUDE.md
non-negotiable — the live API must never make a live call to the source
site). A missing file is surfaced as FileNotFoundError, turned into a clear
404 by the router, never silently faked (CLAUDE.md "never fabricate a
number").
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings


def registry_output_dir() -> Path:
    return Path(get_settings().registry_output_dir)


def load_programme_marigaon() -> dict:
    """Raises FileNotFoundError if scripts/fetch_gt2.py hasn't been run yet
    - caller turns that into a 404."""
    path = registry_output_dir() / "programme_marigaon.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
