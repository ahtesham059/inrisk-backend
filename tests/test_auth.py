from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import create_token, decode_token, hash_password, verify_password
from app.config import Settings, get_runtime_settings
from app.main import app


def test_password_hash_verification():
    encoded = hash_password("correct horse battery staple", b"0123456789abcdef")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("incorrect", encoded)
    assert "correct horse" not in encoded


def test_signed_token_round_trip_and_tampering():
    with patch("app.auth.time.time", return_value=1_000):
        token = create_token("reviewer", "a-long-signing-secret", 10)
        payload = decode_token(token, "a-long-signing-secret")
    assert payload is not None
    assert payload.username == "reviewer"
    assert decode_token(token + "changed", "a-long-signing-secret") is None


def test_expired_token_is_rejected():
    with patch("app.auth.time.time", return_value=1_000):
        token = create_token("reviewer", "a-long-signing-secret", 5)
    with patch("app.auth.time.time", return_value=1_301):
        assert decode_token(token, "a-long-signing-secret") is None


@pytest.mark.asyncio
async def test_login_and_authenticated_identity():
    password_hash = hash_password("correct horse battery staple", b"0123456789abcdef")
    settings = Settings(
        _env_file=None,
        auth_username="reviewer",
        auth_password_hash=password_hash,
        auth_token_secret="a-long-signing-secret-for-tests-only",
    )

    async def settings_override():
        return settings

    app.dependency_overrides[get_runtime_settings] = settings_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rejected = await client.post(
            "/auth/login", json={"username": "reviewer", "password": "wrong"}
        )
        accepted = await client.post(
            "/auth/login",
            json={"username": "reviewer", "password": "correct horse battery staple"},
        )
        identity = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {accepted.json()['access_token']}"}
        )
    app.dependency_overrides.clear()

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert identity.json() == {"username": "reviewer"}
