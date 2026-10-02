from datetime import timedelta

from api.dependencies.rate_limit import Limited, rate_limit
from core import config
from core.security import create_access_token, secret_is_usable, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from schemas.auth import LoginRequest, TokenResponse
from services.rate_limit import LOGIN

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    limited: Limited = Depends(rate_limit(LOGIN, "login attempts")),
) -> TokenResponse:
    # Misconfigured, fail closed: no key to sign with safely, or no password
    # to check against (bcrypt would raise on an empty hash).
    if not secret_is_usable(str(config.SECRET_KEY)) or not config.ADMIN_PASSWORD_HASH:
        logger.error(
            "Admin login refused: SECRET_KEY is unset or too short, or "
            "ADMIN_PASSWORD_HASH is unset"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin login is not configured.",
        )

    if request.username != config.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request.password, config.ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Only a run of failures should lock a client out.
    await limited.reset()
    access_token = create_access_token(
        data={"sub": request.username},
        secret_key=str(config.SECRET_KEY),
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(access_token=access_token)
