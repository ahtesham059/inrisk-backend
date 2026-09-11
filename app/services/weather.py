import json
import re
from datetime import datetime, timezone
from typing import Any

from app.errors import StoredFileInvalidError, StoredFileNotFoundError
from app.schemas import WeatherRequest
from app.services.open_meteo import OpenMeteoClient
from app.storage.base import WeatherStorage

FILE_PATTERN = re.compile(
    r"^weather_-?\d+(?:\.\d+)?_-?\d+(?:\.\d+)?_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}_\d{8}T\d{6}\d{6}Z\.json$"
)


def _coordinate(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def make_filename(request: WeatherRequest) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (
        f"weather_{_coordinate(request.latitude)}_{_coordinate(request.longitude)}_"
        f"{request.start_date.isoformat()}_{request.end_date.isoformat()}_{timestamp}.json"
    )


class WeatherService:
    def __init__(self, client: OpenMeteoClient, storage: WeatherStorage):
        self.client = client
        self.storage = storage

    async def fetch_and_store(self, request: WeatherRequest) -> str:
        content = await self.client.fetch(request)
        name = make_filename(request)
        await self.storage.upload(name, content)
        return name

    async def get_file(self, name: str) -> Any:
        if not FILE_PATTERN.fullmatch(name):
            raise StoredFileNotFoundError
        content = await self.storage.download(name)
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StoredFileInvalidError from exc
        if not isinstance(payload, dict):
            raise StoredFileInvalidError
        return payload
