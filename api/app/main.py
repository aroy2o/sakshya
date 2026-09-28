from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import assets, health, mws, records


def create_app() -> FastAPI:
    settings = get_settings()
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

    photo_dir = Path(settings.photo_storage_dir)
    photo_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/photos", StaticFiles(directory=str(photo_dir)), name="photos")

    return app


app = create_app()
