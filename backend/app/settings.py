from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and backend/.env in development)."""

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./data/moudir.db"
    # Comma-separated origins allowed to call the API cross-origin. Production serves the
    # dashboard and API from one origin (API under /api), so this is normally empty there.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cookie_secure: bool | None = None
    session_ttl_hours: int = 24 * 14
    allow_signup: bool = True
    max_ingest_events: int = 1000
    login_max_failures: int = 10
    login_window_minutes: int = 15
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Hosting providers hand out postgres:// URLs; SQLAlchemy needs the driver named.
        if value.startswith("postgres://"):
            value = "postgresql://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value.removeprefix("postgresql://")
        if value.startswith("sqlite:///./"):
            value = f"sqlite:///{(BASE_DIR / value.removeprefix('sqlite:///./')).resolve()}"
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
