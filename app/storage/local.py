import asyncio
from datetime import datetime, timezone
from pathlib import Path

from app.errors import StorageUnavailableError, StoredFileNotFoundError
from app.storage.base import ObjectMetadata


class LocalWeatherStorage:
    def __init__(self, root: Path):
        self.root = root

    async def upload(self, name: str, content: bytes) -> None:
        def write() -> None:
            self.root.mkdir(parents=True, exist_ok=True)
            target = self.root / name
            with target.open("xb") as stream:
                stream.write(content)

        try:
            await asyncio.to_thread(write)
        except FileExistsError as exc:
            raise StorageUnavailableError("generated filename already exists") from exc
        except OSError as exc:
            raise StorageUnavailableError("local storage is unavailable") from exc

    async def list(self) -> list[ObjectMetadata]:
        def scan() -> list[ObjectMetadata]:
            if not self.root.exists():
                return []
            items = []
            for path in self.root.glob("weather_*.json"):
                stat = path.stat()
                items.append(
                    ObjectMetadata(
                        name=path.name,
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
                    )
                )
            return sorted(items, key=lambda item: item.created_at, reverse=True)

        try:
            return await asyncio.to_thread(scan)
        except OSError as exc:
            raise StorageUnavailableError("local storage is unavailable") from exc

    async def download(self, name: str) -> bytes:
        try:
            return await asyncio.to_thread((self.root / name).read_bytes)
        except FileNotFoundError as exc:
            raise StoredFileNotFoundError from exc
        except OSError as exc:
            raise StorageUnavailableError("local storage is unavailable") from exc
