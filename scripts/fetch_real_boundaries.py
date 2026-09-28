"""
R1 — docs/REAL_DATA_PLAN.md §1, §2 items 1-3, §8's R1 row.

Sources REAL watershed (SLUSI micro-watershed) and district (LGD) boundaries
to replace the Phase 1 placeholder polygon (scripts/data/marigaon_placeholder.geojson),
ranks candidate micro-watersheds for the "treated" demo boundary (since no
human-supplied config/treated_mws.txt exists yet — REAL_DATA_PLAN.md §9
item 2 is still an open human step), and builds a matched-control pool for
R2's watershed-level DiD design (REAL_DATA_PLAN.md §4.1).

Data sources (all real, all free, all documented in docs/DATA_SOURCES.md):
  1. LGD district boundaries — bharatlas.com CC0-1.0 mirror (parquet, 21 MB)
  2. SLUSI micro-watersheds — bharatlas.com CC0-1.0 mirror (parquet, 453 MB —
     see the memory note below for why this is never loaded whole)
  3. ESA WorldCover v200 (2021), 10 m — public AWS Open Data S3 bucket, no
     auth, no Earth Engine — used for crop/built-up/water/tree share
  4. Copernicus DEM GLO-30, 30 m — public AWS Open Data S3 bucket, no auth,
     no Earth Engine — used for mean slope

Why this doesn't need GEE: R2's live Earth Engine analysis is blocked
(PROGRESS.md "Needs your attention" — IAM permission error, human action
required). Every data source this script touches is a *different*, no-auth,
publicly hosted dataset, chosen specifically so R1's boundary work and the
automated candidate ranking can proceed without waiting on that credential.

Memory note (RAM is tight in this environment — see REAL_DATA_PLAN.md's own
warning): the SLUSI parquet (453 MB) is READ VIA duckdb+httpfs with a
bbox-column pushdown filter (`xmin/ymin/xmax/ymax` are plain DOUBLE columns
present in the file, confirmed this session via DESCRIBE) — duckdb prunes
row groups using these before any row is materialized, so a country-wide
bbox query around Assam completes in ~5-50s over HTTP range requests and
never loads the full file into memory. Land-cover/DEM rasters are read via
rasterio's /vsicurl/ windowed reads (also no full-file download) directly
from the COG tiles, clipped to the district bbox needed.

Run:
    python scripts/fetch_real_boundaries.py                 # writes data/real/*, no DB write
    python scripts/fetch_real_boundaries.py --apply-db       # also updates the mws document

Without --apply-db, this is safe to re-run repeatedly for inspection — it
only writes local files under data/real/. With --apply-db, it updates
ONLY three fields on the existing `mws` document (geom, is_synthetic_boundary,
boundary_source) — per this agent's role brief, no other field is touched.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.merge import merge as rasterio_merge
from rasterio.windows import from_bounds
from shapely.geometry import mapping, shape
from shapely.ops import transform as shapely_transform, unary_union
import pyproj

import config
from candidate_ranking import (
    PICK_METHOD_AUTOMATED,
    PICK_METHOD_HUMAN_CONFIRMED,
    CandidateMetrics,
    match_controls,
    rank_candidates,
    select_treated,
)

# REAL_DATA_PLAN.md §9 item 2 / §8's R1 row: "Treated polygon IDs come from
# config/treated_mws.txt (human step); fallback = rank candidates
# automatically." Repo-root config/ (distinct from scripts/config/
# watershed.yaml, which holds the OLD placeholder-era single-boundary
# config) — one SLUSI `id` or `MWS` code per line, '#' comments allowed,
# blank lines ignored. Does not exist yet as of this run (confirmed) —
# every run so far has taken the automated fallback path.
TREATED_MWS_TXT_PATH = config.SCRIPTS_DIR.parent / "config" / "treated_mws.txt"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Politeness: this is a static CC0 data mirror (bharatlas.com), not a
# government portal, but REAL_DATA_PLAN.md's "fetch politely" rule applies
# generally — every raw pull below is cached to disk so re-running this
# script doesn't re-hit the network at all.
_UA = "SAKSHYA-hackathon-research/1.0 (SIH 2026 PS26015; contact via repo)"


# --- duckdb / vector fetch ----------------------------------------------------

def _duckdb_connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("SET memory_limit='3GB'; SET threads=2;")
    try:
        con.execute(f"SET http_user_agent='{_UA}';")
    except Exception:
        logger.debug("This duckdb build doesn't support http_user_agent — continuing without it.")
    return con


def fetch_target_districts(con: duckdb.DuckDBPyConnection) -> dict:
    """Marigaon (the treated district) + every district that spatially
    touches it, within the same state. Cached locally after first fetch."""
    cache_path = config.REAL_DATA_DIR / "districts_marigaon_and_neighbors.geojson"
    if cache_path.exists():
        logger.info("Using cached districts file: %s", cache_path)
        return json.loads(cache_path.read_text())

    logger.info("Fetching LGD district boundaries from %s", config.BHARATLAS_LGD_DISTRICTS_URL)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE state_districts AS
        SELECT dtname, dist_lgd, geometry
        FROM read_parquet('{config.BHARATLAS_LGD_DISTRICTS_URL}')
        WHERE stname ILIKE '%{config.TREATED_STATE_NAME}%'
        """
    )
    treated_rows = con.execute(
        f"SELECT dtname, dist_lgd FROM state_districts WHERE dtname ILIKE '%{_fuzzy(config.TREATED_DISTRICT_NAME)}%'"
    ).fetchall()
    if not treated_rows:
        raise RuntimeError(
            f"No district matching {config.TREATED_DISTRICT_NAME!r} found in "
            f"{config.TREATED_STATE_NAME} — check config.TREATED_DISTRICT_NAME spelling "
            "against the LGD dataset's own dtname values."
        )
    treated_name = treated_rows[0][0]
    logger.info("Treated district resolved to LGD name: %r", treated_name)

    neighbors = con.execute(
        f"""
        SELECT a.dtname, a.dist_lgd
        FROM state_districts a, state_districts m
        WHERE m.dtname = '{treated_name}'
          AND a.dtname != '{treated_name}'
          AND ST_Intersects(ST_Buffer(a.geometry, 0.01), m.geometry)
        """
    ).fetchall()
    logger.info("Found %d neighboring districts: %s", len(neighbors), [n[0] for n in neighbors])

    names = [treated_name] + [n[0] for n in neighbors]
    names_sql = ",".join(f"'{n}'" for n in names)
    rows = con.execute(
        f"""
        SELECT dtname, dist_lgd, ST_AsGeoJSON(geometry)
        FROM state_districts WHERE dtname IN ({names_sql})
        """
    ).fetchall()

    features = []
    for name, lgd, geom_json in rows:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "district": name,
                    "dist_lgd": lgd,
                    "state": config.TREATED_STATE_NAME,
                    "role": "treated_district" if name == treated_name else "neighbor_district",
                },
                "geometry": json.loads(geom_json),
            }
        )
    fc = {
        "type": "FeatureCollection",
        "features": features,
        "_source": {
            "dataset": "LGD district boundaries",
            "url": config.BHARATLAS_LGD_DISTRICTS_URL,
            "licence": "CC0-1.0 / CC-BY-4.0 (bharatlas.com mirror of LGD)",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    config.REAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(fc))
    logger.info("Wrote %s (%d districts)", cache_path, len(features))
    return fc


def _fuzzy(name: str) -> str:
    """LGD spells the target district 'Marigaon'; WDC-PMKSY/common usage
    spells it 'Morigaon'. Strip the vowel that differs so either spelling
    matches (documented ambiguity, REAL_DATA_PLAN.md doesn't resolve it)."""
    return name.replace("a", "%").replace("o", "%")


def fetch_slusi_candidates(con: duckdb.DuckDBPyConnection, districts_fc: dict) -> dict:
    """All SLUSI micro-watersheds intersecting the treated district or any
    neighbor. Cached locally after first fetch (this is the expensive
    query — ~50s against the 453 MB remote parquet, bbox-pruned)."""
    cache_path = config.REAL_DATA_DIR / "raw_cache" / "slusi_candidates_marigaon_and_neighbors.geojson"
    if cache_path.exists():
        logger.info("Using cached SLUSI candidates file: %s", cache_path)
        return json.loads(cache_path.read_text())

    geoms = [shape(f["geometry"]) for f in districts_fc["features"]]
    union = unary_union(geoms)
    xmin, ymin, xmax, ymax = union.bounds
    logger.info("Districts union bbox: %s", (xmin, ymin, xmax, ymax))

    logger.info("Querying SLUSI micro-watersheds from %s (bbox-pruned)...", config.BHARATLAS_SLUSI_MWS_URL)
    con.execute("CREATE OR REPLACE TEMP TABLE districts_union AS SELECT ST_GeomFromText(?) AS geometry", [union.wkt])

    t0 = time.time()
    rows = con.execute(
        f"""
        SELECT s.id, s.AREA, s.CATCHMENT, s.WATERSHED, s.MWS, s.SUBWATERSH,
               s.SUBCATCH, s.region, s.BASIN, ST_AsGeoJSON(s.geometry) geom_json
        FROM read_parquet('{config.BHARATLAS_SLUSI_MWS_URL}') s, districts_union d
        WHERE s.xmin <= {xmax} AND s.xmax >= {xmin} AND s.ymin <= {ymax} AND s.ymax >= {ymin}
          AND ST_Intersects(s.geometry, d.geometry)
        """
    ).fetchall()
    logger.info("Fetched %d candidate micro-watersheds in %.1fs", len(rows), time.time() - t0)

    cols = ["id", "AREA", "CATCHMENT", "WATERSHED", "MWS", "SUBWATERSH", "SUBCATCH", "region", "BASIN", "geom_json"]
    features = []
    for r in rows:
        d = dict(zip(cols, r))
        geom = json.loads(d.pop("geom_json"))
        features.append({"type": "Feature", "properties": d, "geometry": geom})

    fc = {
        "type": "FeatureCollection",
        "features": features,
        "_source": {
            "dataset": "SLUSI micro-watersheds",
            "url": config.BHARATLAS_SLUSI_MWS_URL,
            "licence": "CC0-1.0 (bharatlas.com mirror of SLUSI)",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "caveat": (
                "Third-party mirror of SLUSI data — attribute/code mapping to "
                "SRISHTI's own MWS codes is NOT confirmed (REAL_DATA_PLAN.md §2 "
                "row 1's own flag). MWS codes here (e.g. '3A2D5a3') are SLUSI's "
                "internal scheme, not verified against WDC-PMKSY work-code geodata."
            ),
        },
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(fc))
    logger.info("Wrote %s", cache_path)
    return fc


def _assign_district(candidate_geom, districts_fc: dict) -> str | None:
    """Best-effort: the district with the largest intersection area. Border
    candidates may be ambiguous — this is a labelling convenience for the
    ranking output, not used in any exclusion/scoring math."""
    best_name, best_area = None, 0.0
    for f in districts_fc["features"]:
        dg = shape(f["geometry"])
        if not dg.intersects(candidate_geom):
            continue
        inter_area = dg.intersection(candidate_geom).area
        if inter_area > best_area:
            best_area = inter_area
            best_name = f["properties"]["district"]
    return best_name


# --- raster zonal stats (ESA WorldCover + Copernicus DEM) -------------------

def _read_worldcover(bbox: tuple[float, float, float, float]) -> tuple[np.ndarray, rasterio.Affine]:
    xmin, ymin, xmax, ymax = bbox
    # 3x3 degree tiles named by SW corner. All target districts fall inside
    # one tile (N24E090, covers lon 90-93 / lat 24-27) except a small sliver
    # of Nagaon/West Karbi Anglong past lon 93 — documented limitation,
    # candidates entirely in that sliver get pixel_count=0 and are excluded.
    tile = "N24E090"
    url = f"/vsicurl/{config.ESA_WORLDCOVER_S3_TEMPLATE.format(tile=tile)}"
    logger.info("Reading ESA WorldCover tile %s (windowed to bbox)...", tile)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        with rasterio.open(url) as ds:
            clip_xmax = min(xmax, ds.bounds.right)
            win = from_bounds(xmin, ymin, clip_xmax, ymax, ds.transform)
            arr = ds.read(1, window=win)
            win_transform = ds.window_transform(win)
    logger.info("WorldCover array shape: %s", arr.shape)
    return arr, win_transform


def _dem_tiles_for_bbox(bbox: tuple[float, float, float, float]) -> list[str]:
    xmin, ymin, xmax, ymax = bbox
    import math

    lat0, lat1 = int(math.floor(ymin)), int(math.floor(ymax))
    lon0, lon1 = int(math.floor(xmin)), int(math.floor(xmax))
    tiles = []
    for lat in range(lat0, lat1 + 1):
        for lon in range(lon0, lon1 + 1):
            # Bucket's own tile-name form, confirmed this session via a live
            # HEAD request: "Copernicus_DSM_COG_10_N26_00_E092_00_DEM/...".
            tiles.append(f"N{lat:02d}_00_E{lon:03d}_00")
    return tiles


def _read_dem(bbox: tuple[float, float, float, float]):
    tiles = _dem_tiles_for_bbox(bbox)
    logger.info("Copernicus DEM tiles needed: %s", tiles)
    datasets = []
    used_tiles = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        for tile in tiles:
            url = f"/vsicurl/{config.COPERNICUS_DEM_S3_TEMPLATE.format(tile=tile)}"
            try:
                ds = rasterio.open(url)
                ds.read(1, window=rasterio.windows.Window(0, 0, 1, 1))  # touch one pixel to confirm the tile is actually readable
                ds.close()
                datasets.append(url)
                used_tiles.append(tile)
            except Exception as e:  # noqa: BLE001 — tile may not exist (ocean/border), skip and log
                logger.warning("DEM tile %s unavailable (%s) — skipping, coverage will have a gap there", tile, e)
        if not datasets:
            return None, None
        opened = [rasterio.open(u) for u in datasets]
        mosaic, mosaic_transform = rasterio_merge(opened, bounds=bbox)
        for o in opened:
            o.close()
    logger.info("DEM mosaic shape: %s from tiles %s", mosaic.shape, used_tiles)
    return mosaic[0], mosaic_transform


def _slope_from_dem(dem: np.ndarray, transform: rasterio.Affine, mean_lat_deg: float) -> np.ndarray:
    """Slope in degrees via a simple finite-difference gradient. This is a
    coarse approximation (no edge-aware / curvature-corrected algorithm like
    GDAL's DEMProcessing or richdem) — adequate for a coarse per-candidate
    mean used only in an automated ranking heuristic, documented as such."""
    px_deg_x = transform.a
    px_deg_y = -transform.e
    # Convert degree pixel spacing to meters at this latitude (equirectangular
    # approximation — fine at micro-watershed scale, ~10s of km).
    m_per_deg_lat = 110_574.0
    m_per_deg_lon = 111_320.0 * np.cos(np.radians(mean_lat_deg))
    px_size_x_m = px_deg_x * m_per_deg_lon
    px_size_y_m = px_deg_y * m_per_deg_lat

    dem_f = dem.astype("float32")
    dem_f[dem_f < -1000] = np.nan  # DEM nodata sentinel guard
    dzdy, dzdx = np.gradient(dem_f, px_size_y_m, px_size_x_m)
    slope_rad = np.arctan(np.sqrt(dzdx**2 + dzdy**2))
    return np.degrees(slope_rad)


def compute_candidate_metrics(candidates_fc: dict, districts_fc: dict) -> list[CandidateMetrics]:
    geoms = [shape(f["geometry"]) for f in districts_fc["features"]]
    union = unary_union(geoms)
    bbox = union.bounds

    wc_arr, wc_transform = _read_worldcover(bbox)
    dem_arr, dem_transform = _read_dem(bbox)
    mean_lat = (bbox[1] + bbox[3]) / 2.0
    slope_arr = _slope_from_dem(dem_arr, dem_transform, mean_lat) if dem_arr is not None else None

    # UTM projector for area-accurate hectare computation.
    project = pyproj.Transformer.from_crs("EPSG:4326", config.LOCAL_PROJECTED_CRS, always_xy=True).transform

    # Build a single label raster (WorldCover grid) — one rasterize() call
    # covering all candidates, then one vectorized bincount pass per metric.
    # Much faster than per-candidate masking for hundreds of polygons.
    shapes_labels = []
    id_by_label: dict[int, str] = {}
    valid_features = []
    for i, f in enumerate(candidates_fc["features"], start=1):
        geom = shape(f["geometry"])
        if geom.is_empty:
            continue
        shapes_labels.append((mapping(geom), i))
        id_by_label[i] = f["properties"]["id"]
        valid_features.append((i, f, geom))

    label_raster = rasterize(
        shapes_labels,
        out_shape=wc_arr.shape,
        transform=wc_transform,
        fill=0,
        dtype="int32",
    )

    n_labels = len(valid_features) + 1  # +1 for label 0 (background)
    flat_labels = label_raster.ravel()
    flat_wc = wc_arr.ravel().astype("int32")

    def _class_fraction(class_code: int) -> np.ndarray:
        mask = flat_wc == class_code
        counts = np.bincount(flat_labels[mask], minlength=n_labels)
        return counts

    total_counts = np.bincount(flat_labels, minlength=n_labels).astype("float64")
    total_counts[total_counts == 0] = np.nan  # avoid div-by-zero; results in NaN share for empty labels

    crop_counts = _class_fraction(config.WORLDCOVER_CROP_CLASS)
    built_counts = _class_fraction(config.WORLDCOVER_BUILTUP_CLASS)
    water_counts = _class_fraction(config.WORLDCOVER_WATER_CLASS)
    tree_counts = _class_fraction(config.WORLDCOVER_TREE_CLASS)

    slope_mean_by_label = {}
    if slope_arr is not None:
        # Slope raster may be on a different grid (DEM transform) than the
        # WorldCover label raster — resample the label raster onto the DEM
        # grid via a second rasterize() call at the DEM's resolution/transform.
        label_raster_dem = rasterize(
            shapes_labels, out_shape=slope_arr.shape, transform=dem_transform, fill=0, dtype="int32"
        )
        flat_labels_dem = label_raster_dem.ravel()
        flat_slope = slope_arr.ravel()
        valid = ~np.isnan(flat_slope)
        sums = np.bincount(flat_labels_dem[valid], weights=flat_slope[valid], minlength=n_labels)
        counts = np.bincount(flat_labels_dem[valid], minlength=n_labels).astype("float64")
        with np.errstate(invalid="ignore", divide="ignore"):
            means = sums / counts
        slope_mean_by_label = {lbl: (float(means[lbl]) if counts[lbl] > 0 else None) for lbl in range(1, n_labels)}

    metrics: list[CandidateMetrics] = []
    for label, f, geom in valid_features:
        props = f["properties"]
        total = total_counts[label]
        pixel_count = 0 if np.isnan(total) else int(total)

        area_ha = shapely_transform(project, geom).area / 10_000.0  # m^2 -> ha

        if pixel_count > 0:
            crop_share = float(crop_counts[label] / total)
            built_share = float(built_counts[label] / total)
            water_share = float(water_counts[label] / total)
            tree_share = float(tree_counts[label] / total)
        else:
            crop_share = built_share = water_share = tree_share = 0.0

        metrics.append(
            CandidateMetrics(
                id=props["id"],
                mws_code=props.get("MWS"),
                district=_assign_district(geom, districts_fc),
                area_ha=area_ha,
                crop_share=crop_share,
                built_up_share=built_share,
                water_share=water_share,
                tree_share=tree_share,
                mean_slope_deg=slope_mean_by_label.get(label),
                pixel_count=pixel_count,
            )
        )
    return metrics


def read_human_treated_mws(path: Path = TREATED_MWS_TXT_PATH) -> list[str] | None:
    """Returns a list of SLUSI `id` or `MWS` code strings if a human has
    supplied config/treated_mws.txt, else None (triggering the automated
    fallback). One entry per line, '#' comments and blank lines ignored."""
    if not path.exists():
        return None
    entries = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.append(line)
    if not entries:
        logger.warning("%s exists but has no usable entries — falling back to automated ranking.", path)
        return None
    logger.info("Found human-supplied %s with %d entries — using these as the treated set.", path, len(entries))
    return entries


def _resolve_human_treated(entries: list[str], ranked: list, candidates_fc: dict) -> list:
    """Matches each config/treated_mws.txt entry against candidates by
    `id` first, then by SLUSI `MWS` code. Raises if any entry can't be
    resolved — a silent partial match would be worse than failing loudly
    (CLAUDE.md: never silently produce a plausible-looking wrong answer)."""
    by_id = {r.id: r for r in ranked}
    by_mws_code = {r.mws_code: r for r in ranked if r.mws_code}
    resolved = []
    unresolved = []
    for entry in entries:
        r = by_id.get(entry) or by_mws_code.get(entry)
        if r is None:
            unresolved.append(entry)
        else:
            resolved.append(r)
    if unresolved:
        raise RuntimeError(
            f"config/treated_mws.txt entries not found among fetched candidates: {unresolved} "
            f"(matched against {len(candidates_fc['features'])} candidate id/MWS values — "
            "check spelling, or the candidate wasn't in the fetched district/neighbor set)."
        )
    return resolved


# --- MongoDB write (optional) -------------------------------------------------

def apply_to_mongo(treated_geom_geojson: dict, source_note: str) -> None:
    import pymongo

    from dotenv import load_dotenv
    import os

    load_dotenv(config.SCRIPTS_DIR.parent / ".env")
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27018/sakshya")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client.get_default_database()

    existing = db["mws"].find_one({"_id": config.MWS_ID})
    if existing is None:
        raise RuntimeError(
            f"No mws document with _id={config.MWS_ID!r} found — refusing to create one "
            "here (R1's brief is to update the existing placeholder document's boundary, "
            "not invent a new watershed record)."
        )

    result = db["mws"].update_one(
        {"_id": config.MWS_ID},
        {
            "$set": {
                "geom": treated_geom_geojson,
                "is_synthetic_boundary": False,
                "boundary_source": source_note,
            }
        },
    )
    logger.info(
        "MongoDB mws._id=%s updated: matched=%d modified=%d",
        config.MWS_ID, result.matched_count, result.modified_count,
    )


# --- main ----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="R1: fetch real boundaries, rank treated/control candidates")
    parser.add_argument("--apply-db", action="store_true", help="Also update the mws document in MongoDB")
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="Force recomputing candidate metrics even if data/real/candidate_ranking.json "
        "already exists (the WorldCover+DEM zonal-stats pass takes several minutes — "
        "skipped by default when cached output is already on disk).",
    )
    args = parser.parse_args()

    config.REAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

    ranking_cache = config.REAL_DATA_DIR / "candidate_ranking.json"
    boundary_cache = config.REAL_DATA_DIR / "treated_boundary.geojson"
    if not args.recompute and ranking_cache.exists() and boundary_cache.exists():
        logger.info("Reusing cached %s / %s (pass --recompute to force a fresh run)", ranking_cache.name, boundary_cache.name)
        if args.apply_db:
            treated_boundary_fc = json.loads(boundary_cache.read_text())
            ranking_output = json.loads(ranking_cache.read_text())
            geom_geojson = treated_boundary_fc["geometry"]
            if geom_geojson["type"] == "Polygon":
                geom_geojson = {"type": "MultiPolygon", "coordinates": [geom_geojson["coordinates"]]}
            n_components = len(treated_boundary_fc["properties"]["component_mws_ids"])
            cached_pick_method = ranking_output.get("pick_method", PICK_METHOD_AUTOMATED)
            source_note = (
                f"REAL boundary — union of {n_components} SLUSI micro-watershed polygon(s) "
                f"in {ranking_output['treated_district']} district (pick_method={cached_pick_method}), "
                f"source: {config.BHARATLAS_SLUSI_MWS_URL} (CC0-1.0). "
                + (
                    "Pending human confirmation against the real MARIGAON-WDC-1/2021-22 project's "
                    "actual MWS codes (REAL_DATA_PLAN.md §9 item 2). "
                    if cached_pick_method == PICK_METHOD_AUTOMATED
                    else "Confirmed by config/treated_mws.txt. "
                )
                + f"Applied {datetime.now(timezone.utc).isoformat()} from cached ranking generated {ranking_output['generated_at']}."
            )
            apply_to_mongo(geom_geojson, source_note)
        return

    con = _duckdb_connect()
    districts_fc = fetch_target_districts(con)
    candidates_fc = fetch_slusi_candidates(con, districts_fc)

    logger.info("Computing land-cover + slope zonal stats for %d candidates...", len(candidates_fc["features"]))
    metrics = compute_candidate_metrics(candidates_fc, districts_fc)

    ranked = rank_candidates(metrics)
    treated_district_name = next(
        f["properties"]["district"] for f in districts_fc["features"] if f["properties"]["role"] == "treated_district"
    )
    treated_pool = [r for r in ranked if r.district == treated_district_name]
    treated_ranked_only = rank_candidates(
        [CandidateMetrics(**{k: v for k, v in vars(r).items() if k in CandidateMetrics.__dataclass_fields__}) for r in treated_pool]
    )

    human_entries = read_human_treated_mws()
    if human_entries is not None:
        # Human step done (REAL_DATA_PLAN.md §9 item 2) — use the confirmed
        # set instead of the automated ranking. Resolved against the FULL
        # ranked list (not just treated_pool) since a human-confirmed MWS
        # might legitimately sit just across a district-assignment boundary.
        treated_selection = _resolve_human_treated(human_entries, ranked, candidates_fc)
        pick_method = PICK_METHOD_HUMAN_CONFIRMED
    else:
        treated_selection = select_treated(treated_ranked_only, config.TOP_K_TREATED)
        pick_method = PICK_METHOD_AUTOMATED

    treated_ids = {t.id for t in treated_selection}
    control_pool_candidates = [r for r in ranked if r.district != treated_district_name]
    control_matches = match_controls(
        treated=[CandidateMetrics(**{k: v for k, v in vars(t).items() if k in CandidateMetrics.__dataclass_fields__}) for t in treated_selection],
        pool=control_pool_candidates,
        treated_ids=treated_ids,
    )

    # Union the treated selection's real geometries into the new demo boundary.
    id_to_geom = {f["properties"]["id"]: shape(f["geometry"]) for f in candidates_fc["features"]}
    treated_geoms = [id_to_geom[t.id] for t in treated_selection]
    treated_union = unary_union(treated_geoms) if treated_geoms else None

    ranking_output = {
        "pick_method": pick_method,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "treated_district": treated_district_name,
        "top_k_treated": config.TOP_K_TREATED,
        "method_params": {
            "exclusion": {
                "max_built_up_share": __import__("candidate_ranking").MAX_BUILT_UP_SHARE,
                "max_water_share": __import__("candidate_ranking").MAX_WATER_SHARE,
                "min_area_ha": __import__("candidate_ranking").MIN_AREA_HA,
                "max_area_ha": __import__("candidate_ranking").MAX_AREA_HA,
            },
            "composite_score_weights": {
                "crop_share": __import__("candidate_ranking").WEIGHT_CROP_SHARE,
                "low_built_up": __import__("candidate_ranking").WEIGHT_LOW_BUILT_UP,
                "low_water": __import__("candidate_ranking").WEIGHT_LOW_WATER,
            },
            "control_matching": {
                "crop_share_tolerance_relative": __import__("candidate_ranking").CONTROL_CROP_SHARE_TOLERANCE,
                "slope_tolerance_deg": __import__("candidate_ranking").CONTROL_SLOPE_TOLERANCE_DEG,
                "ndvi_tolerance_relative": __import__("candidate_ranking").CONTROL_NDVI_TOLERANCE,
                "ndvi_match_status": "pending_gee — see PROGRESS.md Needs your attention",
            },
        },
        "data_sources": {
            "districts": config.BHARATLAS_LGD_DISTRICTS_URL,
            "micro_watersheds": config.BHARATLAS_SLUSI_MWS_URL,
            "land_cover": "ESA WorldCover v200 (2021), 10m, public AWS Open Data S3 bucket",
            "elevation": "Copernicus DEM GLO-30, 30m, public AWS Open Data S3 bucket",
        },
        "treated_candidates_all_ranked": [vars(r) for r in treated_ranked_only],
        "treated_selection": [vars(t) for t in treated_selection],
        "control_pool_matches": control_matches,
        "caveats": (
            [
                "AUTOMATED PICK, not confirmed against the real MARIGAON-WDC-1/2021-22 "
                "project's actual micro-watershed codes (REAL_DATA_PLAN.md §9 item 2 is "
                "still an open human step — locate the project on the Srishti/Tejas "
                "Bharat map and supply config/treated_mws.txt to override this)."
            ]
            if pick_method == PICK_METHOD_AUTOMATED
            else [
                f"Treated set confirmed by config/treated_mws.txt ({len(human_entries)} entries) "
                "— NOT the automated ranking fallback."
            ]
        )
        + [
            "SLUSI MWS codes in this output are the third-party mirror's own scheme "
            "— not confirmed to match SRISHTI's official MWS codes.",
            "Slope is a coarse finite-difference approximation, not a GIS-grade "
            "algorithm — adequate only for this ranking heuristic.",
            "Control matching applies crop-share and slope criteria only; NDVI "
            "matching (REAL_DATA_PLAN.md §4.1's third criterion) needs live GEE, "
            "blocked as of this run.",
        ],
    }
    ranking_path = config.REAL_DATA_DIR / "candidate_ranking.json"
    ranking_path.write_text(json.dumps(ranking_output, indent=2, default=str))
    logger.info("Wrote %s", ranking_path)

    if treated_union is not None:
        treated_boundary_fc = {
            "type": "Feature",
            "properties": {
                "mws_id": config.MWS_ID,
                "name": config.MWS_NAME,
                "pick_method": pick_method,
                "source": "SLUSI micro-watersheds (bharatlas.com CC0-1.0 mirror)",
                "component_mws_ids": [t.id for t in treated_selection],
                "component_mws_codes": [t.mws_code for t in treated_selection],
                "is_synthetic_boundary": False,
            },
            "geometry": mapping(treated_union),
        }
        boundary_path = config.REAL_DATA_DIR / "treated_boundary.geojson"
        boundary_path.write_text(json.dumps(treated_boundary_fc, indent=2))
        logger.info("Wrote %s (union of %d real SLUSI polygons)", boundary_path, len(treated_geoms))
    else:
        logger.error("No eligible treated candidates found in %s — cannot build a boundary. See candidate_ranking.json for why every candidate was excluded.", treated_district_name)
        treated_boundary_fc = None

    if args.apply_db:
        if treated_boundary_fc is None:
            raise RuntimeError("Cannot --apply-db: no eligible treated boundary was produced.")
        geom_geojson = treated_boundary_fc["geometry"]
        if geom_geojson["type"] == "Polygon":
            geom_geojson = {"type": "MultiPolygon", "coordinates": [geom_geojson["coordinates"]]}
        source_note = (
            f"REAL boundary — union of {len(treated_geoms)} SLUSI micro-watershed polygon(s) "
            f"in {treated_district_name} district (pick_method={pick_method}), "
            f"source: {config.BHARATLAS_SLUSI_MWS_URL} (CC0-1.0). "
            + (
                "Pending human confirmation against the real MARIGAON-WDC-1/2021-22 project's "
                "actual MWS codes (REAL_DATA_PLAN.md §9 item 2). "
                if pick_method == PICK_METHOD_AUTOMATED
                else "Confirmed by config/treated_mws.txt. "
            )
            + f"Updated {datetime.now(timezone.utc).isoformat()}."
        )
        apply_to_mongo(geom_geojson, source_note)

    logger.info("Done. Treated selection: %d candidates, control pool matches: %d", len(treated_selection), len(control_matches))


if __name__ == "__main__":
    main()
