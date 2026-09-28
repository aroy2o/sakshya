"""App configuration.

Every setting is read from the environment (optionally via a .env file for local
dev). See /.env.example at the repo root for the full documented list — that
file must stay in sync with the fields below (CLAUDE.md's "Environment" section).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Phase 1 — required
    database_url: str

    # Phase 1 — used only by the pytest integration suite, never by the app itself
    database_url_test: str | None = None

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    env: str = "development"
    cors_origins: str = "http://localhost:5173"

    # Photo storage (Phase 1: local disk — swappable for object storage later
    # without a schema change; see CLAUDE.md non-negotiables)
    photo_storage_dir: str = "./app/static/photos"
    photo_public_base_url: str = "http://localhost:8000/static/photos"

    # Demo watershed config path — never hardcoded, per PRD §14 / CLAUDE.md
    seed_watershed_config: str = "scripts/config/watershed.yaml"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
