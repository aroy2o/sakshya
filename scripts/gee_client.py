"""
Thin wrapper around the Earth Engine Python API (`ee`).

This module is the ONLY place `ee.Initialize()` is called anywhere in this
repo. Every other Phase 3 script imports a clean function-call interface
(`build_zones`, `zone_stats`, `seasonal_rainfall`, `fetch_hydrobasin_boundary`)
without needing to care whether GEE is actually reachable in this
environment.

CLAUDE.md non-negotiable: nothing in /api or /web may import this module
or call `ee` directly, ever — precompute-first, offline-only, scripts/-only.

IMPORTANT — status as written: this module's real-GEE code paths are
UNTESTED in this session. No `earthengine-api` package, no GEE service
account key, and no GEE_PROJECT_ID were present in this environment (see
handback report). The structure follows PLAYBOOK.md §8.2's starter code
and standard Earth Engine patterns, but MUST be validated against a live
`ee.Initialize()` the first time real credentials are available, before
its output is trusted for scoring.
"""

from __future__ import annotations

import logging
import os

import config

logger = logging.getLogger(__name__)

_ee = None
_initialized = False


def is_gee_available() -> tuple[bool, str]:
    """
    Cheap, local, no-network precondition check — NOT a live connectivity
    test. Returns (available, reason).

    Checks, in order:
    1. `earthengine-api` package importable.
    2. GEE_PROJECT_ID env var set.
    3. GOOGLE_APPLICATION_CREDENTIALS (service-account key path) set and
       the file exists on disk.
    """
    try:
        import ee  # noqa: F401
    except ImportError:
        return False, "earthengine-api package not installed"

    project_id = os.environ.get("GEE_PROJECT_ID")
    if not project_id:
        return False, "GEE_PROJECT_ID env var not set"

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        return False, "GOOGLE_APPLICATION_CREDENTIALS env var not set"
    if not os.path.isfile(key_path):
        return False, f"GOOGLE_APPLICATION_CREDENTIALS points to a missing file: {key_path}"

    return True, "ok"


def initialize() -> None:
    """Idempotent ee.Initialize() using a service account. Raises if unavailable."""
    global _ee, _initialized
    if _initialized:
        return
    available, reason = is_gee_available()
    if not available:
        raise RuntimeError(f"Earth Engine not available: {reason}")

    import ee

    project_id = os.environ["GEE_PROJECT_ID"]
    key_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    # Service-account auth (non-interactive) — the correct mode for an
    # offline batch script; never a per-developer ee.Authenticate() flow.
    credentials = ee.ServiceAccountCredentials(email=None, key_file=key_path)
    ee.Initialize(credentials, project=project_id)
    _ee = ee
    _initialized = True
    logger.info("Earth Engine initialized for project %s", project_id)


# --- real GEE operations (only usable once initialize() has succeeded) -----

def prep_landsat_collection():
    """Landsat 8/9 SR, cloud/shadow masked, NDVI/MNDWI/NDMI bands added.
    Structure follows PLAYBOOK.md §8.2 exactly, extended with NDMI."""
    initialize()
    ee = _ee

    def _prep(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))  # cloud, shadow
        sr = img.select(["SR_B3", "SR_B4", "SR_B5", "SR_B6"]).multiply(0.0000275).add(-0.2)
        ndvi = sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
        mndwi = sr.normalizedDifference(["SR_B3", "SR_B6"]).rename("MNDWI")
        ndmi = sr.normalizedDifference(["SR_B5", "SR_B6"]).rename("NDMI")
        return ee.Image(
            ndvi.addBands(mndwi).addBands(ndmi).updateMask(clear)
            .copyProperties(img, ["system:time_start"])
        )

    return (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .map(_prep)
    )


def build_zones(lon: float, lat: float, other_points: list[tuple[float, float]]):
    """
    Treated = point.buffer(TREATED_BUFFER_M).
    Control = annulus [CONTROL_RING_INNER_M, CONTROL_RING_OUTER_M] around
    the point, minus every OTHER asset's treated buffer (so no two sites'
    treated/control zones contaminate each other).

    All buffering is done natively in EE (ee.Geometry.buffer() operates in
    meters on the sphere), matching PLAYBOOK §8.2's pattern — no local
    reprojection/shapely math needed for the real-GEE path.

    NOTE (documented, not built this round): PLAYBOOK also suggests masking
    pre-existing water/built-up out of the control ring via ESA WorldCover.
    Not implemented here yet — flagged as a further refinement, since the
    asset-exclusion mask alone already satisfies FR3.1's "vs a control
    zone" requirement; the WorldCover mask is additive precision.
    """
    initialize()
    ee = _ee
    p = ee.Geometry.Point([lon, lat])
    treated = p.buffer(config.TREATED_BUFFER_M)
    control = p.buffer(config.CONTROL_RING_OUTER_M).difference(p.buffer(config.CONTROL_RING_INNER_M))
    for olon, olat in other_points:
        other_buffer = ee.Geometry.Point([olon, olat]).buffer(config.OTHER_ASSET_EXCLUSION_BUFFER_M)
        control = control.difference(other_buffer)
    return treated, control


def zone_stats(geom, start: str, end: str, scale: int = 30) -> dict:
    """Mean NDVI/MNDWI/NDMI over a geometry for a date window, plus a count
    of contributing clear observations (used as an approximate cloud-cover
    signal, not a true 0-1 fraction — refine once exercised against real
    data)."""
    ee = _ee
    coll = prep_landsat_collection().filterBounds(geom).filterDate(start, end)
    comp = coll.median()
    means = comp.reduceRegion(ee.Reducer.mean(), geom, scale, maxPixels=1e9).getInfo()
    obs_count = (
        coll.select("NDVI").count().reduceRegion(ee.Reducer.mean(), geom, scale, maxPixels=1e9).getInfo()
    )
    return {"indices": means, "clear_obs_count": obs_count.get("NDVI", 0)}


def water_fraction(geom, start: str, end: str, scale: int = 30) -> float:
    """Fraction of pixels in geom classified as water (MNDWI > 0) over the window."""
    ee = _ee
    coll = prep_landsat_collection().filterBounds(geom).filterDate(start, end)
    mndwi = coll.select("MNDWI").median()
    water_mask = mndwi.gt(0)
    stats = water_mask.reduceRegion(ee.Reducer.mean(), geom, scale, maxPixels=1e9).getInfo()
    return stats.get("MNDWI", 0.0)


def seasonal_rainfall(geom, start: str, end: str) -> float:
    ee = _ee
    result = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start, end)
        .sum()
        .reduceRegion(ee.Reducer.mean(), geom, 5000)
        .getInfo()
    )
    return result.get("precipitation", 0.0)


def geometry_from_geojson(geojson_geometry: dict):
    """
    Build an ee.Geometry from an arbitrary GeoJSON Polygon/MultiPolygon —
    used by R2's watershed-level analysis (real treated/control MWS
    polygons, not asset point-buffers). `build_zones()` above stays
    point-buffer-only for asset-level scoring (FR3.1); this is the
    polygon-native counterpart for watershed-level DiD
    (REAL_DATA_PLAN.md §4.1).
    """
    initialize()
    ee = _ee
    return ee.Geometry(geojson_geometry)


def fetch_hydrobasin_boundary(hybas_id: int) -> dict:
    """Fetch a HydroBASINS L12 polygon by HYBAS_ID as GeoJSON (fallback MWS
    boundary source per PLAYBOOK §5.3/§5.5, used only when no official MWS
    polygon is available)."""
    initialize()
    ee = _ee
    fc = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_12").filter(
        ee.Filter.eq("HYBAS_ID", hybas_id)
    )
    return fc.getInfo()
