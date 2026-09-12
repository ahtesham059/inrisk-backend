from typing import Any

from fastapi import APIRouter, Depends

from app.auth import require_auth
from app.dependencies import get_weather_service
from app.schemas import StoredFileList, StoreWeatherResponse, WeatherRequest
from app.services.weather import WeatherService

router = APIRouter(tags=["weather"])


@router.post(
    "/store-weather-data", response_model=StoreWeatherResponse, dependencies=[Depends(require_auth)]
)
async def store_weather_data(
    request: WeatherRequest, service: WeatherService = Depends(get_weather_service)
) -> StoreWeatherResponse:
    name = await service.fetch_and_store(request)
    return StoreWeatherResponse(file=name)


@router.get(
    "/list-weather-files", response_model=StoredFileList, dependencies=[Depends(require_auth)]
)
async def list_weather_files(
    service: WeatherService = Depends(get_weather_service),
) -> StoredFileList:
    return StoredFileList(files=await service.storage.list())


@router.get("/weather-file-content/{file_name}", dependencies=[Depends(require_auth)])
async def weather_file_content(
    file_name: str, service: WeatherService = Depends(get_weather_service)
) -> dict[str, Any]:
    return await service.get_file(file_name)
