import pytest
from services.jobs import Worker, dead_letter_stream, enqueue, queue_depth

pytestmark = pytest.mark.anyio

STREAM = "jobs:test"
GROUP = "testers"


def worker(redis, handler, consumer="w1", **kwargs):
    kwargs.setdefault("claim_idle_ms", 60_000)
    return Worker(redis, STREAM, GROUP, consumer, handler, block_ms=10, **kwargs)


async def test_a_job_is_handled_once_and_acknowledged(redis):
    seen = []

    async def handle(job):
        seen.append(job)

    w = worker(redis, handle)
    await w.ensure_group()
    await enqueue(redis, STREAM, {"key": "covers/a.png"})

    assert await w.run_once() == 1
    assert await w.run_once() == 0
    assert seen == [{"key": "covers/a.png"}]
    assert await queue_depth(redis, STREAM, GROUP) == {"lag": 0, "pending": 0}


async def test_jobs_added_before_the_group_existed_are_not_lost(redis):
    seen = []

    async def handle(job):
        seen.append(job["key"])

    await enqueue(redis, STREAM, {"key": "early"})
    w = worker(redis, handle)
    await w.ensure_group()
    await w.ensure_group()  # a second worker starting is fine

    await w.run_once()

    assert seen == ["early"]


async def test_a_failed_job_stays_pending_and_is_retried(redis):
    attempts = []

    async def flaky(job):
        attempts.append(job["key"])
        if len(attempts) == 1:
            raise RuntimeError("R2 hiccup")

    w = worker(redis, flaky, claim_idle_ms=0)
    await w.ensure_group()
    await enqueue(redis, STREAM, {"key": "a"})

    await w.run_once()
    assert (await queue_depth(redis, STREAM, GROUP))["pending"] == 1
    await w.run_once()

    assert attempts == ["a", "a"]
    assert (await queue_depth(redis, STREAM, GROUP))["pending"] == 0


async def test_another_worker_takes_over_a_crashed_workers_job(redis):
    seen = []

    async def handle(job):
        seen.append(job["key"])

    crashed = worker(redis, handle, consumer="crashed")
    await crashed.ensure_group()
    await enqueue(redis, STREAM, {"key": "a"})
    # It read the job and died before acknowledging it.
    await redis.xreadgroup(GROUP, "crashed", {STREAM: ">"}, count=1)

    rescuer = worker(redis, handle, consumer="rescuer", claim_idle_ms=0)
    await rescuer.run_once()

    assert seen == ["a"]
    assert (await queue_depth(redis, STREAM, GROUP))["pending"] == 0


async def test_a_job_that_keeps_failing_goes_to_the_dead_letter_stream(redis):
    async def broken(job):
        raise ValueError("cannot identify image file")

    w = worker(redis, broken, claim_idle_ms=0, max_deliveries=3)
    await w.ensure_group()
    await enqueue(redis, STREAM, {"key": "corrupt.png"})

    for _ in range(4):
        await w.run_once()

    [(_, dead)] = await redis.xrange(dead_letter_stream(STREAM))
    assert dead[b"key"] == b"corrupt.png"
    assert b"cannot identify image file" in dead[b"error"]
    assert (await queue_depth(redis, STREAM, GROUP))["pending"] == 0
    assert await w.run_once() == 0
