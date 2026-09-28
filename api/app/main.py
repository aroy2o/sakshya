from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import ensure_indexes
from app.routers import assets, districts, health, mws, records, thematic


def create_app() -> FastAPI:
    settings = get_settings()
    # Mongo has no migration tool - indexes are declared in code and created
    # idempotently on every boot instead (replaces Alembic's job for the
    # 2dsphere/mws_id/band indexes; there's no schema to migrate otherwise,
    # Mongo is schemaless).
    ensure_indexes()

    app = FastAPI(
        title="SAKSHYA API",
        description=(
            "Analytics layer fusing geo-tagged field photos with satellite evidence "
            "for watershed-work verification. See /docs/PRD.md for the full spec."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(mws.router)
    app.include_router(records.router)
    app.include_router(assets.router)
    app.include_router(thematic.router)
    app.include_router(districts.router)

    photo_dir = Path(settings.photo_storage_dir)
    photo_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/photos", StaticFiles(directory=str(photo_dir)), name="photos")

    # geospatial-engineer's precompute output (scripts/output/) — owned by
    # another agent's pipeline, so check_dir=False: a fresh checkout that
    # hasn't run Phase 3's precompute yet must not crash the whole API at
    # startup, it should just 404 on thematic/satellite requests until it
    # exists.
    geospatial_dir = Path(settings.geospatial_output_dir)
    app.mount(
        "/static/geospatial", StaticFiles(directory=str(geospatial_dir), check_dir=False), name="geospatial"
    )

    return app


app = create_app()
