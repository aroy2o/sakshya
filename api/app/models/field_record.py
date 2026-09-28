"""DRISHTI-style field record model — PRD.md §8.

`is_synthetic` and `photo_source` are non-negotiable per CLAUDE.md: every
non-real record MUST have is_synthetic=true, and whenever it does,
photo_source MUST also be set.
"""

from __future__ import annotations

import datetime as dt

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FieldRecord(Base):
    __tablename__ = "field_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_code: Mapped[str | None] = mapped_column(String, nullable=True)
    mws_id: Mapped[str] = mapped_column(String, ForeignKey("mws.id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    activity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    gps_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    orientation: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    photo1_url: Mapped[str | None] = mapped_column(String, nullable=True)
    photo2_url: Mapped[str | None] = mapped_column(String, nullable=True)
    photo1_phash: Mapped[str | None] = mapped_column(String, nullable=True)
    photo2_phash: Mapped[str | None] = mapped_column(String, nullable=True)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    observer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    observer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    organisation: Mapped[str | None] = mapped_column(String, nullable=True)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    photo_source: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
