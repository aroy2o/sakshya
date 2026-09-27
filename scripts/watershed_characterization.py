"""
FR3.2 — watershed characterization: drainage network with Strahler stream
order + slope from DEM, LULC snapshot. Exported as GeoJSON/PNG per
watershed. Run OFFLINE ONLY (CLAUDE.md precompute-first).

Also produces the manifest behind FR3.3's GET /mws/{id}/thematic/{layer}:
backend-engineer's endpoint does a keyed lookup into
output/{mws_id}/thematic/manifest.json rather than touching GEE.

Coordinator ruling (this round): PRD §9's thematic-layer enum is frozen at
exactly 6 keys — drainage, lulc, ndvi_before, ndvi_after, ndvi_change,
water. `slope.png` is still produced (useful for the Phase 6 report card)
but is filed under manifest["supporting_artifacts"], NOT
manifest["layers"] — it is not exposed via the endpoint and no 7th enum
key was added.

Real-GEE path status: NOT implemented this round. Building it correctly
(MERIT Hydro flow-accumulation export -> local whitebox-tools Strahler
extraction -> GeoJSON; SRTM slope -> geemap.ee_export_image; ESA
WorldCover clip -> geemap.ee_export_image with a legend; Landsat
before/after/change NDVI composites -> geemap.ee_export_image) needs GEE
credentials to write AND validate against, which this session doesn't
have. Rather than ship untested raster-export code, `generate(placeholder=False)`
raises NotImplementedError with the intended pipeline documented inline,
so whoever picks this up next (possibly me, next round) has a concrete
starting point instead of a blank page.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path

from PIL import Image, ImageDraw

import config
import gee_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PLACEHOLDER_SIZE = (512, 512)


def _placeholder_png(path: Path, label: str, color: tuple[int, int, int]) -> None:
    img = Image.new("RGB", PLACEHOLDER_SIZE, color)
    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        (20, 20),
        f"PLACEHOLDER\n{label}\nGEE credentials required\nnot real satellite data",
        fill=(255, 255, 255),
    )
    img.save(path)


def _load_boundary() -> dict:
    boundary_path = config.OUTPUT_DIR / "placeholder_boundary.geojson"
    if not boundary_path.exists():
        raise FileNotFoundError(
            f"No boundary found at {boundary_path} — run precompute_gee.py first "
            "(it self-generates a placeholder boundary if none exists), or point "
            "this script at backend-engineer's real seed boundary."
        )
    return json.loads(boundary_path.read_text())


def _boundary_bounds(boundary: dict) -> list[float]:
    coords = boundary["geometry"]["coordinates"][0]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return [min(xs), min(ys), max(xs), max(ys)]


def _placeholder_drainage_geojson(boundary: dict) -> dict:
    """A minimal synthetic 3-segment dendritic network (order 1, 1 -> 2)
    purely to exercise the GeoJSON shape end-to-end. NOT a real drainage
    network — real extraction needs MERIT Hydro + local whitebox-tools
    (see module docstring)."""
    bounds = _boundary_bounds(boundary)
    cx = (bounds[0] + bounds[2]) / 2
    cy = (bounds[1] + bounds[3]) / 2
    span = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
    d = span * 0.3
    features = [
        {
            "type": "Feature",
            "properties": {"stream_id": 1, "strahler_order": 1, "placeholder": True},
            "geometry": {"type": "LineString", "coordinates": [[cx - d, cy - d], [cx, cy]]},
        },
        {
            "type": "Feature",
            "properties": {"stream_id": 2, "strahler_order": 1, "placeholder": True},
            "geometry": {"type": "LineString", "coordinates": [[cx + d, cy - d], [cx, cy]]},
        },
        {
            "type": "Feature",
            "properties": {"stream_id": 3, "strahler_order": 2, "placeholder": True},
            "geometry": {"type": "LineString", "coordinates": [[cx, cy], [cx, cy + d]]},
        },
    ]
    return {"type": "FeatureCollection", "features": features, "placeholder": True}


def _placeholder_lulc_stats() -> dict:
    return {
        "placeholder": True,
        "source": "synthetic_no_gee_credentials",
        "classes_pct": {
            "cropland": None,
            "tree_cover": None,
            "built_up": None,
            "grassland": None,
            "water": None,
        },
        "note": "Not computed — real values need ESA WorldCover v200 via GEE.",
    }


def _generate_real(boundary: dict) -> None:
    """
    Intended real pipeline (documented, not built this round):

    1. Drainage + Strahler order:
       - Pull MERIT Hydro (`MERIT/Hydro/v1_0_1`) flow-accumulation band for
         the MWS extent via geemap.ee_export_image (one GEE round-trip).
       - Threshold flow-accumulation locally (e.g. > ~1 km^2 contributing
         area) to extract a stream raster.
       - Run whitebox.WhiteboxTools().StrahlerStreamOrder() locally on the
         thresholded stream + D8 flow-direction rasters (also from MERIT
         Hydro) to get an ordered stream raster.
       - Vectorize to LineStrings (whitebox's RasterStreamsToVector or
         rasterio+shapely) with strahler_order as a per-feature property.
       Rationale: Strahler ordering is a recursive graph algorithm that
       doesn't map onto GEE's map-reduce model — this keeps GEE to a single
       raw-data pull and does the graph algorithm in ordinary local Python.

    2. Slope: SRTM 30 m (`USGS/SRTMGL1_003`) -> ee.Terrain.slope() ->
       geemap.ee_export_image() as a colorized PNG clipped to the MWS
       extent, plus min/max/mean stats.

    3. LULC: ESA WorldCover v200 (`ESA/WorldCover/v200`) clipped to the MWS
       boundary -> geemap.ee_export_image() as a colorized PNG using
       WorldCover's own legend, plus a `lulc_stats.json` of % area per class
       via reduceRegion(frequencyHistogram).

    4. NDVI before/after/change: Landsat 8/9 median composites for
       config.BASELINE_START/END and config.LATEST_START/END (via
       gee_client.prep_landsat_collection), visualized with a diverging
       NDVI palette, exported via geemap.ee_export_image() for
       ndvi_before.png / ndvi_after.png, with a pixel-difference image for
       ndvi_change.png. Same pattern for water.png from MNDWI > 0.

    Not implemented here: needs GEE credentials to write AND validate
    against — see gee_client.py's module docstring for why untested
    raster-export code isn't being shipped speculatively.
    """
    raise NotImplementedError(
        "Real watershed-characterization pipeline needs GEE credentials "
        "(none available this session) — see this function's docstring for "
        "the documented pipeline to implement once credentials exist."
    )


def generate(placeholder: bool = True) -> Path:
    config.THEMATIC_DIR.mkdir(parents=True, exist_ok=True)
    boundary = _load_boundary()

    if not placeholder:
        _generate_real(boundary)  # always raises for now — see docstring

    drainage = _placeholder_drainage_geojson(boundary)
    (config.THEMATIC_DIR / "drainage.geojson").write_text(json.dumps(drainage, indent=2))

    lulc_stats = _placeholder_lulc_stats()
    (config.THEMATIC_DIR / "lulc_stats.json").write_text(json.dumps(lulc_stats, indent=2))

    bounds = _boundary_bounds(boundary)

    # PRD §9's frozen 6-key thematic-layer enum — servable via
    # GET /mws/{id}/thematic/{layer}.
    servable_specs = [
        ("lulc.png", "lulc", (60, 120, 60)),
        ("ndvi_before.png", "ndvi_before", (90, 130, 60)),
        ("ndvi_after.png", "ndvi_after", (70, 150, 70)),
        ("ndvi_change.png", "ndvi_change", (140, 90, 140)),
        ("water_latest.png", "water", (50, 90, 160)),
    ]
    # NOT part of the frozen enum — coordinator ruling this round: produce
    # it for the Phase 6 report card, don't expose it via the endpoint.
    supporting_specs = [
        ("slope.png", "slope", (120, 100, 80)),
    ]

    manifest = {
        "mws_id": config.MWS_ID,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "placeholder": True,
        "source": "synthetic_no_gee_credentials",
        "layers": {},
        "supporting_artifacts": {},
    }

    for filename, key, color in servable_specs:
        _placeholder_png(config.THEMATIC_DIR / filename, key, color)
        manifest["layers"][key] = {
            "type": "raster_png",
            "path": filename,
            "bounds": bounds,
            "placeholder": True,
        }
    manifest["layers"]["drainage"] = {
        "type": "geojson",
        "path": "drainage.geojson",
        "placeholder": True,
    }

    for filename, key, color in supporting_specs:
        _placeholder_png(config.THEMATIC_DIR / filename, key, color)
        manifest["supporting_artifacts"][key] = {
            "type": "raster_png",
            "path": filename,
            "bounds": bounds,
            "note": (
                "Not exposed via GET /mws/{id}/thematic/{layer} — PRD §9's "
                "enum is frozen at 6 keys (coordinator ruling); kept for the "
                "Phase 6 watershed report card."
            ),
            "placeholder": True,
        }

    config.THEMATIC_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    logger.info(
        "Wrote thematic manifest (%d servable layers + %d supporting artifacts) to %s",
        len(manifest["layers"]), len(manifest["supporting_artifacts"]), config.THEMATIC_DIR,
    )
    return config.THEMATIC_MANIFEST_PATH


if __name__ == "__main__":
    gee_ok, reason = gee_client.is_gee_available()
    if not gee_ok:
        logger.warning("GEE not available (%s) — generating placeholder thematic layers.", reason)
    generate(placeholder=not gee_ok)
