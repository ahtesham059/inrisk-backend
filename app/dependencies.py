from functools import lru_cache

from app.config import get_settings
from app.services.open_meteo import OpenMeteoClient
from app.services.weather import WeatherService
from app.storage.local import LocalWeatherStorage
from app.storage.supabase import SupabaseWeatherStorage


@lru_cache
def _build_weather_service() -> WeatherService:
    settings = get_settings()
    if settings.storage_backend == "supabase":
        if not settings.supabase_url or not settings.supabase_server_key:
            raise RuntimeError("Supabase storage requires SUPABASE_URL and SUPABASE_SECRET_KEY")
        storage = SupabaseWeatherStorage(
            settings.supabase_url,
            settings.supabase_server_key,
            settings.supabase_bucket,
            settings.request_timeout_seconds,
        )
    elif settings.storage_backend == "local" and settings.app_environment != "production":
        storage = LocalWeatherStorage(settings.local_storage_path)
    else:
        raise RuntimeError("Production requires STORAGE_BACKEND=supabase")

    return WeatherService(
        OpenMeteoClient(settings.open_meteo_url, settings.request_timeout_seconds),
        storage,
        settings.max_stored_files,
    )


async def get_weather_service() -> WeatherService:
    return _build_weather_service()
