"""GET /mws/{id}/thematic/{layer} — PRD §9 / FR3.3.

PRD §9 only says this endpoint returns "Tile URL or GeoJSON" without an
envelope shape. frontend-engineer already built (and committed) a
`kind: 'raster' | 'vector'` discriminated-union envelope against this exact
PRD line (web/src/schemas/domain.ts's zThematicLayerResponse) - matched here
field-for-field so frontend's zod parsing doesn't reject a real response.

One deliberate, flagged gap: frontend's schema names the raster field
`tile_url` (implying an XYZ tile pyramid, `{z}/{x}/{y}`). What geospatial-
engineer's precompute actually produces is a single bounds-anchored PNG per
layer, not a tile pyramid - so `tile_url` here is a single static image URL,
meant to be rendered via a bounds-based image overlay (MapLibre ImageSource),
not a RasterSource with a tile template. Left as-is (matching the committed
field name) rather than unilaterally renamed - flagged to the coordinator for
frontend-engineer to reconcile the rendering approach.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class LegendEntry(BaseModel):
    color: str
    label: str


class ThematicLayerOut(BaseModel):
    layer: str
    kind: Literal["raster", "vector"]
    bounds: tuple[float, float, float, float]
    legend: list[LegendEntry]
    tile_url: str | None = None
    geojson: dict[str, Any] | None = None
    # Additive over frontend's current schema (silently stripped by zod's
    # non-strict .parse() until they opt in to reading it) - surfaces
    # geospatial-engineer's own placeholder/synthetic flag from the manifest,
    # per CLAUDE.md's synthetic-data-transparency non-negotiable.
    placeholder: bool = True
