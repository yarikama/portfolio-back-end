"""
POST /ask: a visitor's question about the owner's work, answered as a
server-sent event stream:

    event: token   data: {"text": "..."}          a piece of the answer
    event: done    data: {"citations": [...]}     the sources it cited
    event: error   data: {"detail": "..."}        the answer broke off

Errors before the first token (limits, model down) are ordinary JSON
responses with a status code instead.
"""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import asdict

import httpx
from api.dependencies.rate_limit import rate_limit
from core import config
from db.dependency import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from schemas.ask import AskRequest
from services.ask import REQUESTS, Answer, ModelUnavailableError, cited, snapshot
from services.rate_limit import ASK, ASK_ALL, ASK_ALL_CLIENTS
from sqlalchemy.orm import Session

router = APIRouter()

# Created lazily: a semaphore belongs to the event loop that first uses it.
_generating: asyncio.Semaphore | None = None


def generating() -> asyncio.Semaphore:
    global _generating
    if _generating is None:
        _generating = asyncio.Semaphore(config.ASK_MAX_CONCURRENT)
    return _generating


def unavailable(detail: str, retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
        headers={"Retry-After": str(retry_after)},
    )


def event(name: str, data: dict) -> str:
    # JSON keeps newlines in the answer from ending the event early.
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/ask",
    # The visitor's own limit first: a visitor over it does not use up the
    # site's daily budget.
    dependencies=[
        Depends(rate_limit(ASK, "questions")),
        Depends(
            rate_limit(ASK_ALL, "questions on the site today", client=ASK_ALL_CLIENTS)
        ),
    ],
)
async def ask(body: AskRequest, db: Session = Depends(get_db)):
    slots = generating()
    if slots.locked():
        REQUESTS.labels("busy").inc()
        raise unavailable("Busy answering other questions. Try again shortly.", 10)

    answer = Answer(snapshot(db), body.question)
    events = stream(answer, slots)
    try:
        # Runs the stream up to its connection to the model, so a model
        # that is down is still a plain 503 rather than a broken stream.
        await events.__anext__()
    except ModelUnavailableError as error:
        REQUESTS.labels("unavailable").inc()
        logger.warning(f"Ask: model unavailable: {error}")
        raise unavailable(
            "The assistant is offline right now. Try again later.", 60
        ) from error

    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def stream(answer: Answer, slots: asyncio.Semaphore) -> AsyncIterator[str]:
    """
    The GPU slot and the model connection are taken inside the generator,
    and the route starts it before returning: from then on its cleanup runs
    however the response ends, even if the visitor leaves before the first
    byte is sent and the response never iterates it.
    """
    async with slots:
        try:
            await answer.open()
            yield ""  # connected; the route takes this, the visitor never sees it
            started = time.perf_counter()
            async for piece in answer.tokens():
                yield event("token", {"text": piece})
            citations = cited(answer.text, answer.snapshot.sources)
            yield event("done", {"citations": [asdict(s) for s in citations]})
            REQUESTS.labels("answered").inc()
            # The question is logged (Loki keeps it for its retention
            # period) to see what visitors ask; the visitor's address is not.
            logger.info(
                f"Ask: answered in {time.perf_counter() - started:.1f}s, "
                f"{answer.output_tokens} tokens, cited "
                f"{[s.id for s in citations]}: {answer.question!r}"
            )
        except (httpx.HTTPError, ValueError) as error:
            REQUESTS.labels("error").inc()
            logger.error(f"Ask: answer broke off: {error!r}")
            yield event("error", {"detail": "The answer broke off. Try again."})
        finally:
            # Also runs when the visitor leaves mid-answer: closing the
            # connection makes vLLM stop generating.
            await answer.close()
