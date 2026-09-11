import json
from typing import Any

import httpx

from app.errors import UpstreamWeatherError
from app.schemas import WeatherRequest

DAILY_VARIABLES = (
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
)


class OpenMeteoClient:
    def __init__(self, url: str, timeout: float = 20):
        self.url = url
        self.timeout = timeout

    async def fetch(self, request: WeatherRequest) -> bytes:
        params = {
            "latitude": request.latitude,
            "longitude": request.longitude,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "daily": ",".join(DAILY_VARIABLES),
            "temperature_unit": "celsius",
            "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.url, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamWeatherError("weather provider request failed") from exc

        self._validate_payload(payload)
        return json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")

    @staticmethod
    def _validate_payload(payload: Any) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("daily"), dict):
            raise UpstreamWeatherError("weather provider returned an invalid response")
        daily = payload["daily"]
        dates = daily.get("time")
        if not isinstance(dates, list):
            raise UpstreamWeatherError("weather provider returned no daily dates")
        for variable in DAILY_VARIABLES:
            values = daily.get(variable)
            if not isinstance(values, list) or len(values) != len(dates):
                raise UpstreamWeatherError("weather provider returned incomplete daily data")
