import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_runtime_settings

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
bearer = HTTPBearer(auto_error=False)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt, expected = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME or int(iterations) != PASSWORD_ITERATIONS:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), _b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(actual, _b64decode(expected))
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class TokenPayload:
    username: str
    expires_at: int


def create_token(username: str, secret: str, ttl_minutes: int) -> str:
    payload = _b64encode(
        json.dumps(
            {"sub": username, "exp": int(time.time()) + ttl_minutes * 60},
            separators=(",", ":"),
        ).encode()
    )
    signature = _b64encode(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def decode_token(token: str, secret: str) -> TokenPayload | None:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64encode(
            hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_b64decode(payload))
        username = data["sub"]
        expires_at = int(data["exp"])
        if not isinstance(username, str) or expires_at <= int(time.time()):
            return None
        return TokenPayload(username, expires_at)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_runtime_settings),
) -> str:
    username, _, secret = settings.require_auth_config()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="authentication required")
    payload = decode_token(credentials.credentials, secret)
    if payload is None or not hmac.compare_digest(payload.username, username):
        raise HTTPException(status_code=401, detail="invalid or expired session")
    return payload.username
