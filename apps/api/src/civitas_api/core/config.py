from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Civitas API"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    database_url: str = "postgresql://localhost/postgres"
    civitas_postgis_dsn: str = ""

    supabase_jwt_secret: str = ""
    civitas_internal_api_key: str = ""
    storage_bucket: str = "report-media"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.is_production and not self.supabase_jwt_secret.strip():
            raise ValueError("SUPABASE_JWT_SECRET is required when CIVITAS_ENV=production")
        if self.is_production and not self.civitas_internal_api_key.strip():
            raise ValueError("CIVITAS_INTERNAL_API_KEY is required when CIVITAS_ENV=production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
