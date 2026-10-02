from typing import Annotated

from core import config
from core.security import decode_access_token
from fastapi import Depends, HTTPException, Request, status
from loguru import logger
from services import admin_session

# Requests that only read. Any other method sent with the session cookie
# must come from one of the site's own pages (CORS_ORIGINS): the cookie is
# SameSite=Strict already, and this also holds if a browser ignores that.
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def bearer_admin(request: Request) -> str | None:
    """
    The admin named by a valid password-login token. Kept while the site
    moves to Google sign-in; to be removed with password login.
    """
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    payload = decode_access_token(token, str(config.SECRET_KEY))
    if payload is None or payload.get("sub") != config.ADMIN_USERNAME:
        return None
    return payload["sub"]


async def session_admin(request: Request) -> str | None:
    """
    The account signed in with the session cookie, if it still may.
    Raises 503 if Redis cannot be reached: the session can't be checked.
    """
    token = request.cookies.get(admin_session.COOKIE)
    redis = getattr(request.app.state, "redis", None)
    if not token or redis is None:
        return None
    try:
        email = await admin_session.lookup(redis, token)
    except Exception as error:
        logger.warning(f"Admin session unavailable: {error!r}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporarily unavailable. Try again shortly.",
            headers={"Retry-After": "30"},
        ) from error
    # Removed from ADMIN_EMAILS since signing in: out at once.
    if email is None or email not in config.ADMIN_EMAILS:
        return None
    return email


async def current_admin(request: Request) -> str | None:
    """The admin making the request, or None for a visitor."""
    email = await session_admin(request)
    if email is not None:
        if (
            request.method not in SAFE_METHODS
            and request.headers.get("Origin") not in config.CORS_ORIGINS
        ):
            return None
        return email
    return bearer_admin(request)


async def get_current_admin(request: Request) -> str:
    admin = await current_admin(request)
    if admin is None:
        raise unauthorized("Not signed in")
    return admin


CurrentAdmin = Annotated[str, Depends(get_current_admin)]
