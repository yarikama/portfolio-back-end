"""
Per-client rate limits kept in Redis, shared by every replica of the API.

Each check is one Lua script, so reading the count, deciding and recording
the request happen atomically: two requests arriving together cannot both
see the last free slot. Design, alternatives and trade-offs: homelab
docs/11-rate-limiting.md.
"""

import ipaddress
import math
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger
from prometheus_client import Counter
from redis.asyncio import Redis
from redis.exceptions import RedisError

DECISIONS = Counter(
    "rate_limit_decisions_total",
    "Requests checked against a rate limit, by rule and outcome.",
    ["rule", "decision"],
)
ERRORS = Counter(
    "rate_limit_errors_total",
    "Checks that could not reach Redis, by rule.",
    ["rule"],
)


class Algorithm(Enum):
    # Exact: remembers every request in the window. Memory grows with the
    # limit, so only for small limits (a handful of logins or messages).
    SLIDING_LOG = "sliding_log"
    # Constant memory, allows a burst up to the limit, then a steady rate.
    TOKEN_BUCKET = "token_bucket"


@dataclass(frozen=True)
class Rule:
    name: str
    # At most `limit` requests per `window` seconds. For a token bucket:
    # a burst of `limit`, refilled at limit/window per second.
    limit: int
    window: float
    algorithm: Algorithm
    # When Redis cannot be reached: let requests through, or refuse them.
    fail_open: bool


# Guessing the admin password. Every attempt counts; a successful login
# clears the count, so only a run of failures blocks.
LOGIN = Rule("login", 5, 15 * 60, Algorithm.SLIDING_LOG, fail_open=False)
# Contact form messages, which go straight into the database.
CONTACT = Rule("contact", 3, 60 * 60, Algorithm.SLIDING_LOG, fail_open=True)
# Every other public request. A page load makes a few API calls; 60 at once
# and one a second after that is far beyond a person browsing.
PUBLIC = Rule("public", 60, 60, Algorithm.TOKEN_BUCKET, fail_open=True)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    remaining: int
    # Seconds until the next request would be allowed; 0 when allowed.
    retry_after: float


class LimiterUnavailableError(Exception):
    """Redis could not be reached for a rule that fails closed."""


# KEYS[1]: sorted set of request times (ms). ARGV: limit, window (ms), now
# (ms, empty for Redis's own clock), a unique member for this request.
# Rejected requests are not recorded, so a client that keeps trying is
# let in again as soon as its oldest request leaves the window.
SLIDING_LOG_SCRIPT = """
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
if not now then
  local t = redis.call('TIME')
  now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
end
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
local count = redis.call('ZCARD', KEYS[1])
if count < limit then
  redis.call('ZADD', KEYS[1], now, ARGV[4])
  redis.call('PEXPIRE', KEYS[1], window)
  return {1, limit - count - 1, 0}
end
local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
return {0, 0, tonumber(oldest[2]) + window - now}
"""

# KEYS[1]: hash with the tokens left and when they were counted. ARGV:
# capacity, refill rate (tokens per ms), now (ms, empty for Redis's clock).
# Tokens are fractional; tostring keeps the fraction when storing them.
TOKEN_BUCKET_SCRIPT = """
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
if not now then
  local t = redis.call('TIME')
  now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
end
local state = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(state[1]) or capacity
local ts = tonumber(state[2]) or now
tokens = math.min(capacity, tokens + math.max(0, now - ts) * rate)
local allowed = 0
local retry = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
else
  retry = math.ceil((1 - tokens) / rate)
end
redis.call('HSET', KEYS[1], 'tokens', tostring(tokens), 'ts', tostring(now))
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / rate))
return {allowed, math.floor(tokens), retry}
"""


class RateLimiter:
    def __init__(
        self, redis: Redis, clock: Optional[Callable[[], float]] = None
    ) -> None:
        # clock (seconds) is for tests; by default the time comes from Redis,
        # so every replica measures windows against the same clock.
        self._redis = redis
        self._clock = clock
        self._sliding_log = redis.register_script(SLIDING_LOG_SCRIPT)
        self._token_bucket = redis.register_script(TOKEN_BUCKET_SCRIPT)

    @staticmethod
    def key(rule: Rule, client: str) -> str:
        return f"ratelimit:{rule.name}:{client}"

    async def hit(self, rule: Rule, client: str) -> Decision:
        """Count one request from `client` against `rule`."""
        now = "" if self._clock is None else str(int(self._clock() * 1000))
        window_ms = int(rule.window * 1000)
        try:
            if rule.algorithm is Algorithm.SLIDING_LOG:
                reply = await self._sliding_log(
                    keys=[self.key(rule, client)],
                    args=[rule.limit, window_ms, now, secrets.token_hex(8)],
                )
            else:
                reply = await self._token_bucket(
                    keys=[self.key(rule, client)],
                    args=[rule.limit, repr(rule.limit / window_ms), now],
                )
        except (RedisError, OSError) as error:
            ERRORS.labels(rule.name).inc()
            logger.warning(f"Rate limit {rule.name}: Redis unavailable: {error!r}")
            if rule.fail_open:
                return Decision(allowed=True, remaining=rule.limit, retry_after=0)
            raise LimiterUnavailableError from error

        allowed, remaining, retry_ms = (int(value) for value in reply)
        decision = Decision(bool(allowed), remaining, retry_ms / 1000)
        DECISIONS.labels(rule.name, "allowed" if allowed else "rejected").inc()
        if not decision.allowed:
            logger.warning(
                f"Rate limit {rule.name}: rejected {client}, "
                f"retry in {decision.retry_after:.0f}s"
            )
        return decision

    async def reset(self, rule: Rule, client: str) -> None:
        """Forget `client`'s requests under `rule` (after a successful login)."""
        try:
            await self._redis.delete(self.key(rule, client))
        except (RedisError, OSError) as error:
            # The failures age out of the window on their own.
            logger.warning(f"Rate limit {rule.name}: reset failed: {error!r}")


def retry_after_header(decision: Decision) -> str:
    """Whole seconds, rounded up, as Retry-After requires."""
    return str(max(1, math.ceil(decision.retry_after)))


def client_id(headers: Mapping[str, str], peer: Optional[str]) -> str:
    """
    Who a request counts against.

    Production traffic arrives through Cloudflare Tunnel and Traefik, so the
    peer address is Traefik's pod; the visitor's address is in
    CF-Connecting-IP, which Cloudflare sets itself (a client cannot supply
    its own). Only Traefik can reach the API (NetworkPolicy), so the header
    cannot be forged by skipping Cloudflare. Without it (local development)
    the peer is the client.

    IPv6 addresses are grouped by /64: one connection usually gets a whole
    /64, so counting single addresses would let a client rotate through
    billions of them.
    """
    raw = headers.get("cf-connecting-ip") or peer or "unknown"
    try:
        address = ipaddress.ip_address(raw.strip())
    except ValueError:
        return raw[:64]
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return str(address.ipv4_mapped)
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return str(address)
