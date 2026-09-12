from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ObjectMetadata:
    name: str
    size: int
    created_at: str


class WeatherStorage(Protocol):
    async def upload(self, name: str, content: bytes) -> None: ...

    async def list(self) -> list[ObjectMetadata]: ...

    async def download(self, name: str) -> bytes: ...

    async def delete(self, name: str) -> None: ...
