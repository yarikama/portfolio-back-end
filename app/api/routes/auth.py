from datetime import timedelta

from api.dependencies.rate_limit import Limited, rate_limit
from core import config
from core.security import create_access_token, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.auth import LoginRequest, TokenResponse
from services.rate_limit import LOGIN

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    limited: Limited = Depends(rate_limit(LOGIN, "login attempts")),
) -> TokenResponse:
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
