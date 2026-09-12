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
    auth_username: str | None = None
    auth_password_hash: str | None = None
    auth_token_secret: str | None = None
    auth_token_ttl_minutes: int = Field(default=120, ge=5, le=1440)
    max_stored_files: int = Field(default=100, ge=1, le=10_000)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supabase_server_key(self) -> str | None:
        return self.supabase_secret_key or self.supabase_service_role_key

    def require_auth_config(self) -> tuple[str, str, str]:
        if not self.auth_username or not self.auth_password_hash or not self.auth_token_secret:
            raise RuntimeError(
                "Authentication requires AUTH_USERNAME, AUTH_PASSWORD_HASH, and AUTH_TOKEN_SECRET"
            )
        if len(self.auth_token_secret) < 32:
            raise RuntimeError("AUTH_TOKEN_SECRET must contain at least 32 characters")
        return self.auth_username, self.auth_password_hash, self.auth_token_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_runtime_settings() -> Settings:
    return get_settings()
