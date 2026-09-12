import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.errors import (
    StorageLimitError,
    StorageUnavailableError,
    StoredFileInvalidError,
    StoredFileNotFoundError,
    UpstreamWeatherError,
)
from app.routes.auth import router as auth_router
from app.routes.weather import router

logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(title="InRisk Weather API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(router)


def error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    messages = [str(item["msg"]).removeprefix("Value error, ") for item in exc.errors()]
    return error(400, "; ".join(messages))


@app.exception_handler(StoredFileNotFoundError)
async def not_found(_: Request, __: StoredFileNotFoundError) -> JSONResponse:
    return error(404, "not found")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error(404, "not found")
    return error(exc.status_code, str(exc.detail))


@app.exception_handler(UpstreamWeatherError)
async def upstream_error(_: Request, exc: UpstreamWeatherError) -> JSONResponse:
    return error(502, str(exc))


@app.exception_handler(StorageUnavailableError)
async def storage_error(_: Request, exc: StorageUnavailableError) -> JSONResponse:
    return error(503, str(exc))


@app.exception_handler(StorageLimitError)
async def storage_limit(_: Request, exc: StorageLimitError) -> JSONResponse:
    return error(429, str(exc))


@app.exception_handler(StoredFileInvalidError)
async def invalid_stored_file(_: Request, __: StoredFileInvalidError) -> JSONResponse:
    return error(500, "stored file contains invalid JSON")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
