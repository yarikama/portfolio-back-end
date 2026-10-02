import os

import pytest
from fakeredis import FakeAsyncRedis
from redis.asyncio import Redis

# A signing key for the tests, set before any test module imports the app's
# configuration: the app refuses to sign or accept tokens with a missing or
# short one.
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-the-test-suite-only-0123456789"
)


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
