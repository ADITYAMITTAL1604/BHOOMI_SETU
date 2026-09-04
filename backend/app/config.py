"""Pydantic v2 settings management for BhoomiSetu backend."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is read from environment variables (or .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./bhoomisetu.db"

    # ── Auth ──────────────────────────────────────────────────────────────────
    jwt_secret: str = "changeme_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7

    # ── Environment & Data Source ─────────────────────────────────────────────
    environment: str = "development"
    data_source: str = "synthetic"  # "synthetic" | "project"

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Storage ───────────────────────────────────────────────────────────────
    document_storage_path: str = "/app/storage/documents"
    ml_model_path: str = "/app/ml/models"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    def validate_secrets(self) -> None:
        if self.is_production and self.jwt_secret == "changeme_in_production":
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: "
                "JWT_SECRET cannot be default 'changeme_in_production' when ENVIRONMENT is 'production'. "
                "Set a secure, random JWT_SECRET in your production environment."
            )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call this everywhere instead of Settings()."""
    return Settings()
