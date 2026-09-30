import os

import pytest
from fakeredis import FakeAsyncRedis
from redis.asyncio import Redis


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def redis():
    """
    fakeredis (with real Lua) by default; a real Redis when REDIS_TEST_URL
    points at one, as in CI. That database is flushed.
    """
    url = os.environ.get("REDIS_TEST_URL")
    client = Redis.from_url(url) if url else FakeAsyncRedis()
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()
