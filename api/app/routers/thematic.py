"""GET /mws/{id}/thematic/{layer} — PRD §9 / FR3.3.

Serves geospatial-engineer's precomputed output only (scripts/output/) - never
calls Earth Engine live (precompute-first non-negotiable, CLAUDE.md).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from shapely.geometry import shape

from app.config import get_settings
from app.db import get_db
from app.models.mws import COLLECTION as MWS_COLLECTION
from app.schemas.thematic import LegendEntry, ThematicLayerOut
from app.services import geospatial_output
from app.services.geospatial_output import THEMATIC_LAYERS

router = APIRouter(tags=["thematic"])

# Legend metadata: not part of geospatial-engineer's manifest (which only
# carries type/path/bounds/placeholder), so this is presentation-only
# cartographic convention defined here - not a scientific claim, so it's fine
# for this module to own it rather than treating it as a "fabricated number."
_LEGENDS: dict[str, list[LegendEntry]] = {
    "drainage": [LegendEntry(color="#0ea5e9", label="Drainage line (Strahler stream order)")],
    "lulc": [
        LegendEntry(color="#a6611a", label="Built-up / bare"),
        LegendEntry(color="#dfc27d", label="Cropland"),
        LegendEntry(color="#80cdc1", label="Forest / tree cover"),
        LegendEntry(color="#018571", label="Water"),
    ],
    "ndvi_before": [
        LegendEntry(color="#a50026", label="Low NDVI"),
        LegendEntry(color="#fee08b", label="Medium NDVI"),
        LegendEntry(color="#1a9850", label="High NDVI"),
    ],
    "ndvi_after": [
        LegendEntry(color="#a50026", label="Low NDVI"),
        LegendEntry(color="#fee08b", label="Medium NDVI"),
        LegendEntry(color="#1a9850", label="High NDVI"),
    ],
    "ndvi_change": [
        LegendEntry(color="#d73027", label="NDVI decrease"),
        LegendEntry(color="#f7f7f7", label="No change"),
        LegendEntry(color="#1a9850", label="NDVI increase"),
    ],
    "water": [
        LegendEntry(color="#f0f0f0", label="No water"),
        LegendEntry(color="#2166ac", label="Surface water"),
    ],
}


@router.get("/mws/{mws_id}/thematic/{layer}", response_model=ThematicLayerOut)
def get_thematic_layer(mws_id: str, layer: str, db: Database = Depends(get_db)) -> ThematicLayerOut:
    if layer not in THEMATIC_LAYERS:
        raise HTTPException(404, f"unknown layer {layer!r} - must be one of {THEMATIC_LAYERS}")

    mws_doc = db[MWS_COLLECTION].find_one({"_id": mws_id}, {"geom": 1})
    if mws_doc is None:
        raise HTTPException(404, f"mws {mws_id!r} not found")

    try:
        manifest = geospatial_output.load_thematic_manifest(mws_id)
    except FileNotFoundError:
        raise HTTPException(404, f"no precomputed thematic output for mws {mws_id!r} yet") from None

    entry = manifest.get("layers", {}).get(layer)
    if entry is None:
        raise HTTPException(404, f"layer {layer!r} not present in mws {mws_id!r}'s manifest")

    manifest_placeholder = bool(manifest.get("placeholder", False))
    placeholder = bool(entry.get("placeholder", manifest_placeholder))

    # Manifest's raster entries carry their own bounds; the vector (drainage)
    # entry doesn't (a GeoJSON's geometry is self-describing) - fall back to
    # the mws polygon's own bounding box, which is the semantically correct
    # extent for a watershed-wide vector layer anyway.
    if "bounds" in entry:
        bounds = tuple(entry["bounds"])
    else:
        bounds = tuple(shape(mws_doc["geom"]).bounds)

    legend = _LEGENDS.get(layer, [])

    if entry["type"] == "raster_png":
        settings = get_settings()
        tile_url = f"{settings.thematic_public_base_url.rstrip('/')}/{mws_id}/thematic/{entry['path']}"
        return ThematicLayerOut(
            layer=layer,
            kind="raster",
            bounds=bounds,
            legend=legend,
            tile_url=tile_url,
            placeholder=placeholder,
        )

    if entry["type"] == "geojson":
        try:
            geojson = geospatial_output.load_thematic_geojson(mws_id, entry["path"])
        except FileNotFoundError:
            raise HTTPException(
                404, f"manifest references {entry['path']!r} for layer {layer!r} but the file is missing"
            ) from None
        return ThematicLayerOut(
            layer=layer, kind="vector", bounds=bounds, legend=legend, geojson=geojson, placeholder=placeholder
        )

    raise HTTPException(500, f"manifest layer {layer!r} has unrecognized type {entry['type']!r}")
