from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Civitas API"
    environment: str = Field(default="development", validation_alias="CIVITAS_ENV")
    cors_origins: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    database_url: str = "postgresql://localhost/postgres"
    civitas_postgis_dsn: str = ""
    workflow_checkpoint_database_url: str = Field(
        default="", validation_alias="CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL"
    )

    civitas_internal_api_key: str = ""
    storage_bucket: str = "report-media"

    groq_api_key: str = ""
    llm_primary_model: str = Field(
        default="openai/gpt-oss-120b", validation_alias="CIVITAS_LLM_PRIMARY_MODEL"
    )
    llm_fast_model: str = Field(
        default="openai/gpt-oss-20b", validation_alias="CIVITAS_LLM_FAST_MODEL"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", extra="ignore", populate_by_name=True
    )

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.database_url and self.database_url.strip() != "postgresql://localhost/postgres":
            if not self.civitas_postgis_dsn:
                self.civitas_postgis_dsn = self.database_url.strip()
            if not self.workflow_checkpoint_database_url:
                self.workflow_checkpoint_database_url = self.database_url.strip()

        if not self.is_production:
            return self

        missing: list[str] = []
        required = {
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
            "CIVITAS_POSTGIS_DSN": self.civitas_postgis_dsn,
            "CIVITAS_INTERNAL_API_KEY": self.civitas_internal_api_key,
            "CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL": self.workflow_checkpoint_database_url,
            "GROQ_API_KEY": self.groq_api_key,
        }
        for name, value in required.items():
            if not value.strip():
                missing.append(name)

        if (
            not self.database_url.strip()
            or self.database_url.strip() == "postgresql://localhost/postgres"
        ):
            missing.append("DATABASE_URL")

        if missing:
            raise ValueError(
                "Missing required production configuration: " + ", ".join(sorted(missing))
            )
        if "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must not contain '*' when CIVITAS_ENV=production")
        if not self.cors_origin_list or any(
            origin.startswith(("http://localhost", "http://127.0.0.1"))
            for origin in self.cors_origin_list
        ):
            raise ValueError("CORS_ORIGINS must contain explicit production origins")
        if not self.supabase_jwt_secret.strip() and not self.supabase_url.strip():
            raise ValueError(
                "Production authentication requires SUPABASE_URL for JWKS verification "
                "or SUPABASE_JWT_SECRET for legacy HS256 verification"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
