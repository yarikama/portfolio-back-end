from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.config import METRICS_PORT, REDIS_URL, SECRET_KEY
from core.security import MIN_SECRET_LENGTH, secret_is_usable
from fastapi import FastAPI
from loguru import logger
from prometheus_client import start_http_server
from redis.asyncio import Redis
from services.rate_limit import RateLimiter


def connect_redis(url: str, socket_timeout: float = 0.25) -> Redis:
    # Redis answers in well under a millisecond in the cluster. Short
    # timeouts keep a hung Redis from holding requests: the check fails and
    # the rule's fail-open or fail-closed choice decides instead.
    return Redis.from_url(
        url,
        socket_timeout=socket_timeout,
        socket_connect_timeout=0.25,
        health_check_interval=30,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if METRICS_PORT:
        start_http_server(METRICS_PORT)
    if not secret_is_usable(str(SECRET_KEY)):
        # The API still serves the site; only the admin is shut.
        logger.error(
            f"SECRET_KEY is unset or shorter than {MIN_SECRET_LENGTH} characters: "
            "admin login and admin tokens are refused"
        )

    redis = None
    if str(REDIS_URL):
        redis = connect_redis(str(REDIS_URL))
        app.state.redis = redis
        app.state.rate_limiter = RateLimiter(redis)
    else:
        logger.warning("REDIS_URL is not set: requests are not rate limited")
    try:
        yield
    finally:
        if redis is not None:
            await redis.aclose()
