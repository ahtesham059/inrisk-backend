import hmac

from fastapi import APIRouter, Depends, HTTPException

from app.auth import create_token, require_auth, verify_password
from app.config import Settings, get_runtime_settings
from app.schemas import AuthenticatedUser, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, settings: Settings = Depends(get_runtime_settings)
) -> LoginResponse:
    username, password_hash, secret = settings.require_auth_config()
    valid_username = hmac.compare_digest(request.username, username)
    valid_password = verify_password(request.password, password_hash)
    if not valid_username or not valid_password:
        raise HTTPException(status_code=401, detail="invalid username or password")
    return LoginResponse(
        access_token=create_token(username, secret, settings.auth_token_ttl_minutes),
        expires_in=settings.auth_token_ttl_minutes * 60,
    )


@router.get("/me", response_model=AuthenticatedUser)
async def current_user(username: str = Depends(require_auth)) -> AuthenticatedUser:
    return AuthenticatedUser(username=username)
