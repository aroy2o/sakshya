from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.common import GeoFlagOut

# Fixed per PRD §15.1 - do not invent new codes.
CATEGORY_CODES = {"AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"}

# photo_source enum per PRD §8's column comment: 'field' | 'ai_generated' | 'stock_cc' | 'unknown'
PHOTO_SOURCES_SYNTHETIC = {"ai_generated", "stock_cc", "unknown"}
PHOTO_SOURCE_REAL = "field"


class FieldRecordIn(BaseModel):
    """POST /records JSON metadata part (submitted alongside multipart photo1/photo2)."""

    work_code: str | None = None
    mws_id: str
    category: str
    activity: str
    status: str | None = None
    lat: float
    lon: float
    gps_accuracy_m: float | None = None
    orientation: float | None = None
    captured_at: dt.datetime | None = None
    remarks: str | None = None
    observer_id: str | None = None
    observer_name: str | None = None
    organisation: str | None = None
    is_synthetic: bool = False
    photo_source: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> FieldRecordIn:
        if self.category not in CATEGORY_CODES:
            raise ValueError(f"category must be one of {sorted(CATEGORY_CODES)}, got {self.category!r}")

        # is_synthetic <-> photo_source pairing: CLAUDE.md non-negotiable
        # ("is_synthetic is never optional... photo_source goes with it")
        # combined with PRD §8's column comment enumerating the allowed values.
        if self.is_synthetic:
            if not self.photo_source or self.photo_source not in PHOTO_SOURCES_SYNTHETIC:
                raise ValueError(
                    "photo_source is required and must be one of "
                    f"{sorted(PHOTO_SOURCES_SYNTHETIC)} when is_synthetic=true"
                )
        elif self.photo_source is None:
            self.photo_source = PHOTO_SOURCE_REAL
        return self


class FieldRecordOut(BaseModel):
    id: int
    work_code: str | None
    mws_id: str
    category: str
    activity: str
    status: str | None
    lat: float
    lon: float
    gps_accuracy_m: float | None
    orientation: float | None
    captured_at: dt.datetime | None
    photo1_url: str | None
    photo2_url: str | None
    photo1_phash: str | None
    photo2_phash: str | None
    remarks: str | None
    observer_id: str | None
    observer_name: str | None
    organisation: str | None
    is_synthetic: bool
    photo_source: str | None
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class GeoIntegrityOut(BaseModel):
    geo_score: int
    geo_flags: list[GeoFlagOut]


class RecordIngestOut(BaseModel):
    record: FieldRecordOut
    geo_integrity: GeoIntegrityOut
