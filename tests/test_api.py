import json
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_weather_service
from app.errors import StoredFileNotFoundError, UpstreamWeatherError
from app.main import app
from app.schemas import WeatherRequest
from app.services.weather import WeatherService
from app.storage.base import ObjectMetadata

SAMPLE = {
    "latitude": 28.6,
    "longitude": 77.2,
    "timezone": "Asia/Kolkata",
    "daily_units": {
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
        "apparent_temperature_max": "°C",
        "apparent_temperature_min": "°C",
    },
    "daily": {
        "time": ["2025-01-01"],
        "temperature_2m_max": [20.0],
        "temperature_2m_min": [10.0],
        "apparent_temperature_max": [19.0],
        "apparent_temperature_min": [9.0],
    },
}


class FakeClient:
    async def fetch(self, _: WeatherRequest) -> bytes:
        return json.dumps(SAMPLE).encode()


class FailingClient:
    async def fetch(self, _: WeatherRequest) -> bytes:
        raise UpstreamWeatherError("weather provider request failed")


class FakeStorage:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    async def upload(self, name: str, content: bytes) -> None:
        self.objects[name] = content

    async def list(self) -> list[ObjectMetadata]:
        return [
            ObjectMetadata(name=name, size=len(data), created_at="2025-01-02T00:00:00Z")
            for name, data in self.objects.items()
        ]

    async def download(self, name: str) -> bytes:
        try:
            return self.objects[name]
        except KeyError as exc:
            raise StoredFileNotFoundError from exc


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
async def client(storage: FakeStorage):
    async def service_override():
        return WeatherService(FakeClient(), storage)

    app.dependency_overrides[get_weather_service] = service_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


def payload(**overrides):
    base = {
        "latitude": 28.6139,
        "longitude": 77.209,
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
    }
    return {**base, **overrides}


@pytest.mark.parametrize(
    "change",
    [
        {"latitude": 91},
        {"latitude": True},
        {"longitude": -181},
        {"start_date": "2025-01-31", "end_date": "2025-01-01"},
        {"start_date": "2025-01-01", "end_date": "2025-02-01"},
        {"start_date": "not-a-date"},
    ],
)
async def test_rejects_invalid_requests(client: AsyncClient, change: dict):
    response = await client.post("/store-weather-data", json=payload(**change))
    assert response.status_code == 400
    assert response.json()["status"] == "error"


async def test_stores_lists_and_returns_full_json(client: AsyncClient, storage: FakeStorage):
    stored = await client.post("/store-weather-data", json=payload())
    assert stored.status_code == 200
    name = stored.json()["file"]
    assert name.startswith("weather_28.6139_77.209_2025-01-01_2025-01-31_")
    assert json.loads(storage.objects[name]) == SAMPLE

    listed = await client.get("/list-weather-files")
    assert listed.status_code == 200
    assert listed.json()["files"][0]["name"] == name

    content = await client.get(f"/weather-file-content/{name}")
    assert content.status_code == 200
    assert content.json() == SAMPLE


async def test_missing_or_invalid_file_uses_exact_404(client: AsyncClient):
    for name in ("bad.json", "weather_1_2_2025-01-01_2025-01-01_20250101T000000000000Z.json"):
        response = await client.get(f"/weather-file-content/{name}")
        assert response.status_code == 404
        assert response.json() == {"status": "error", "message": "not found"}


async def test_upstream_failure_does_not_upload(storage: FakeStorage):
    async def service_override():
        return WeatherService(FailingClient(), storage)

    app.dependency_overrides[get_weather_service] = service_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/store-weather-data", json=payload())
    app.dependency_overrides.clear()
    assert response.status_code == 502
    assert storage.objects == {}


def test_same_day_is_valid():
    request = WeatherRequest(
        latitude=0,
        longitude=0,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 1),
    )
    assert request.start_date == request.end_date
