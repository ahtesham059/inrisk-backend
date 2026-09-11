from urllib.parse import quote

import httpx

from app.errors import StorageUnavailableError, StoredFileNotFoundError
from app.storage.base import ObjectMetadata


class SupabaseWeatherStorage:
    def __init__(self, url: str, key: str, bucket: str, timeout: float = 20):
        self.base_url = url.rstrip("/")
        self.bucket = bucket
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        self.timeout = timeout

    async def upload(self, name: str, content: bytes) -> None:
        url = f"{self.base_url}/storage/v1/object/{quote(self.bucket)}/{quote(name)}"
        headers = {**self.headers, "Content-Type": "application/json", "x-upsert": "false"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, content=content)
            if response.status_code not in (200, 201):
                raise StorageUnavailableError("cloud storage upload failed")
        except httpx.HTTPError as exc:
            raise StorageUnavailableError("cloud storage is unavailable") from exc

    async def list(self) -> list[ObjectMetadata]:
        url = f"{self.base_url}/storage/v1/object/list/{quote(self.bucket)}"
        result: list[ObjectMetadata] = []
        offset = 0
        limit = 100
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while True:
                    response = await client.post(
                        url,
                        headers={**self.headers, "Content-Type": "application/json"},
                        json={
                            "prefix": "",
                            "limit": limit,
                            "offset": offset,
                            "sortBy": {"column": "created_at", "order": "desc"},
                            "search": "weather_",
                        },
                    )
                    response.raise_for_status()
                    page = response.json()
                    for item in page:
                        metadata = item.get("metadata") or {}
                        result.append(
                            ObjectMetadata(
                                name=item["name"],
                                size=int(metadata.get("size") or 0),
                                created_at=item.get("created_at") or item.get("updated_at") or "",
                            )
                        )
                    if len(page) < limit:
                        break
                    offset += limit
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise StorageUnavailableError("cloud storage listing failed") from exc
        return result

    async def download(self, name: str) -> bytes:
        url = f"{self.base_url}/storage/v1/object/{quote(self.bucket)}/{quote(name)}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
            if response.status_code == 404:
                raise StoredFileNotFoundError
            response.raise_for_status()
            return response.content
        except StoredFileNotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise StorageUnavailableError("cloud storage download failed") from exc
