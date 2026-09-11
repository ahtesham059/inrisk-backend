import pytest

from app.errors import UpstreamWeatherError
from app.services.open_meteo import OpenMeteoClient


def test_rejects_misaligned_daily_arrays():
    payload = {
        "daily": {
            "time": ["2025-01-01"],
            "temperature_2m_max": [],
            "temperature_2m_min": [1],
            "apparent_temperature_max": [1],
            "apparent_temperature_min": [1],
        }
    }
    with pytest.raises(UpstreamWeatherError):
        OpenMeteoClient._validate_payload(payload)
