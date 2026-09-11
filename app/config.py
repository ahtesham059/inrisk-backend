from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_environment: str = "development"
    storage_backend: str = "local"
    local_storage_path: Path = Path(".data/weather")
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_bucket: str = "weather-data"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    open_meteo_url: str = "https://archive-api.open-meteo.com/v1/archive"
    request_timeout_seconds: float = Field(default=20, gt=0, le=60)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supabase_server_key(self) -> str | None:
        return self.supabase_secret_key or self.supabase_service_role_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
