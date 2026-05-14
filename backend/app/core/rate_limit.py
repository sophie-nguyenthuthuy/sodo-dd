"""Redis-backed token-bucket limiter, keyed by API key ID."""

from __future__ import annotations

import time

import redis

from app.config import settings

_redis: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
    return _redis


_LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now_ms = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(bucket[1])
local ts = tonumber(bucket[2])

if tokens == nil then
  tokens = burst
  ts = now_ms
end

local delta_ms = math.max(0, now_ms - ts)
local refill = (delta_ms / 60000.0) * rate
tokens = math.min(burst, tokens + refill)

local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', key, 120000)

return {allowed, tokens}
"""


def check_rate_limit(scope: str) -> tuple[bool, float]:
    """Returns (allowed, remaining_tokens)."""
    client = _get_redis()
    now_ms = int(time.time() * 1000)
    rate = settings.rate_limit_per_minute
    burst = settings.rate_limit_burst
    key = f"rl:{scope}"
    res = client.eval(_LUA_TOKEN_BUCKET, 1, key, rate, burst, now_ms)  # type: ignore[no-untyped-call]
    allowed, remaining = int(res[0]), float(res[1])
    return allowed == 1, remaining
