"""Micro-watershed model — PRD.md §8.

Demo uses HydroBASINS L12 as a stand-in for official MWS polygons; see
`is_synthetic_boundary`.
"""

from __future__ import annotations

import datetime as dt

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MWS(Base):
    __tablename__ = "mws"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False
    )
    baseline_start: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    baseline_end: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    latest_start: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    latest_end: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    is_synthetic_boundary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
