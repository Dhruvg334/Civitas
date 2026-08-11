from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Civitas API"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    # Optional — defaults to DATABASE_URL when empty
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Required for persistence. Same value used by the geospatial package
    # via CIVITAS_POSTGIS_DSN; we mirror it here for direct backend use.
    database_url: str = "postgresql://localhost/postgres"
    civitas_postgis_dsn: str = ""

    # Auth + storage
    supabase_jwt_secret: str = ""
    storage_bucket: str = "report-media"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()