from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import joblib
from core.config import MEMOIZATION_FLAG, METRICS_PORT, REDIS_URL
from fastapi import FastAPI
from loguru import logger
from prometheus_client import start_http_server
from redis.asyncio import Redis
from services.rate_limit import RateLimiter


def preload_model():
    """
    In order to load model on memory to each worker
    """
    from services.predict import MachineLearningModelHandlerScore

    MachineLearningModelHandlerScore.get_model(joblib.load)


def connect_redis(url: str) -> Redis:
    # Redis answers in well under a millisecond in the cluster. Short
    # timeouts keep a hung Redis from holding requests: the check fails and
    # the rule's fail-open or fail-closed choice decides instead.
    return Redis.from_url(
        url,
        socket_timeout=0.25,
        socket_connect_timeout=0.25,
        health_check_interval=30,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if MEMOIZATION_FLAG:
        preload_model()
    if METRICS_PORT:
        start_http_server(METRICS_PORT)

    redis = None
    if str(REDIS_URL):
        redis = connect_redis(str(REDIS_URL))
        app.state.rate_limiter = RateLimiter(redis)
    else:
        logger.warning("REDIS_URL is not set: requests are not rate limited")
    try:
        yield
    finally:
        if redis is not None:
            await redis.aclose()
