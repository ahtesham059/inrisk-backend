import math
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class WeatherRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    latitude: float
    longitude: float
    start_date: date
    end_date: date

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def reject_boolean_coordinates(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("coordinates must be numbers")
        return value

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not math.isfinite(value) or not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not math.isfinite(value) or not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "WeatherRequest":
        if self.start_date < date(1940, 1, 1):
            raise ValueError("start_date must be on or after 1940-01-01")
        if self.end_date > date.today():
            raise ValueError("end_date cannot be in the future")
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if (self.end_date - self.start_date).days + 1 > 31:
            raise ValueError("date range cannot exceed 31 days")
        return self


class StoredFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    size: int
    created_at: str


class StoredFileList(BaseModel):
    files: list[StoredFile]


class StoreWeatherResponse(BaseModel):
    status: str = "ok"
    file: str


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
