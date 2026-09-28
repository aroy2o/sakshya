"""App configuration.

Every setting is read from the environment (optionally via a .env file for local
dev). See /.env.example at the repo root for the full documented list — that
file must stay in sync with the fields below (CLAUDE.md's "Environment" section).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Phase 1 — required. MongoDB connection string (includes the db name as
    # the URI path, e.g. mongodb://localhost:27018/sakshya) - switched from
    # Postgres+PostGIS per explicit human decision (see CLAUDE.md "DB:" line
    # and PRD.md §8's proposed rewrite). No Atlas/cloud credentials exist in
    # this environment; api/docker-compose.yml runs a local mongod instead.
    mongo_uri: str

    # Used only by the pytest integration suite, never by the app itself.
    mongo_uri_test: str | None = None

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

    # Phase 3 — geospatial-engineer's precompute output root (thematic layer
    # manifests/rasters/geojson + per-record satellite_results.json). Read-only
    # from the API's perspective — never written to, never computed live here
    # (precompute-first non-negotiable). Resolved relative to the process's cwd,
    # same convention as photo_storage_dir (run the API from /api).
    geospatial_output_dir: str = "../scripts/output"
    thematic_public_base_url: str = "http://localhost:8000/static/geospatial"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
