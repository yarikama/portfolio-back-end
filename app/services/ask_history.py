"""
The last few turns of a visitor's conversation with the chat, so a
follow-up ("what about the second one?") makes sense to the model.

Kept in Redis, not sent by the browser: the browser only holds a random
conversation id, so a visitor cannot forge what "the assistant said
earlier". A conversation keeps its last HISTORY_TURNS turns and expires
HISTORY_TTL_SECONDS after its latest question. Redis keeps no data across
restarts, and a restart only means the next question starts afresh; if
Redis is down, questions are answered without history.
"""

import json
import re
import secrets
from dataclasses import asdict, dataclass

from loguru import logger
from redis.asyncio import Redis

HISTORY_TURNS = 2
HISTORY_TTL_SECONDS = 30 * 60
# What new_id() makes; anything else from the browser is not looked up.
CONVERSATION_ID = re.compile(r"^[A-Za-z0-9_-]{22}$")


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str
    # The page of a highlighted passage, if the question was about one. The
    # passage itself is left out: the answer already explains it, and the
    # room in the context is better kept for the documents.
    page: str | None = None


def new_id() -> str:
    return secrets.token_urlsafe(16)  # 22 characters


def key(conversation: str) -> str:
    return f"ask:conversation:{conversation}"


async def load(redis: Redis | None, conversation: str | None) -> list[Turn]:
    """The conversation's earlier turns, oldest first; none if it is
    unknown, expired, malformed, or Redis can't be reached."""
    if redis is None or not conversation or not CONVERSATION_ID.match(conversation):
        return []
    try:
        raw = await redis.lrange(key(conversation), 0, -1)
        return [Turn(**json.loads(item)) for item in raw]
    except Exception as error:
        logger.warning(f"Ask: conversation history unavailable: {error!r}")
        return []


async def save(redis: Redis | None, conversation: str, turn: Turn) -> None:
    """Add a turn, keep the last HISTORY_TURNS, and restart the expiry."""
    if redis is None:
        return
    try:
        async with redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key(conversation), json.dumps(asdict(turn), ensure_ascii=False))
            pipe.ltrim(key(conversation), -HISTORY_TURNS, -1)
            pipe.expire(key(conversation), HISTORY_TTL_SECONDS)
            await pipe.execute()
    except Exception as error:
        logger.warning(f"Ask: could not keep the conversation: {error!r}")
