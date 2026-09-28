"""Schemas shared across more than one router."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    """Loosely-typed GeoJSON geometry input.

    Coordinates are validated structurally by shapely at the point of use
    (app/routers/mws.py) rather than re-implementing full GeoJSON typing here
    — keeps Phase 1 dependency-light. `type` is restricted to the two shapes
    PRD §8's mws.geom column can hold after coercion (Polygon is auto-wrapped
    into a MultiPolygon of one part).
    """

    type: Literal["Polygon", "MultiPolygon"]
    coordinates: list[Any]


class GeoFlagOut(BaseModel):
    """Mirrors PRD §8's `geo_flags` JSONB shape, extended with points/max
    (additive over the PRD's {rule, passed, detail} comment; JSONB is
    untyped in the schema so this isn't a schema deviation) so the FR5.3 UI
    checklist can render partial credit without re-deriving it."""

    rule: str
    passed: bool
    points: int
    max: int = Field(..., description="Maximum points available for this rule")
    detail: str


class AssetFeatureProperties(BaseModel):
    id: int
    work_code: str | None
    category: str
    activity: str
    status: str | None
    captured_at: dt.datetime | None
    photo1_url: str | None
    is_synthetic: bool
    evidence_score: int | None
    band: str | None


class AssetFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: AssetFeatureProperties


class AssetFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[AssetFeature]
