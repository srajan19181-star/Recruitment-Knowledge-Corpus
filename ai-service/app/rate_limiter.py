"""
Sliding-window rate limiter backed by Redis sorted sets executed atomically
via Lua script to eliminate race conditions between checking count and adding.
"""

import time
import uuid

from app.config import settings
from app.redis_client import build_redis_client

_redis = build_redis_client()

# Atomically prune expired entries, check current count, and append current timestamp
LUA_SLIDING_WINDOW = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local window_start = now - window

redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
local current_count = redis.call('ZCARD', key)

if current_count >= limit then
    return 0
else
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, math.ceil(window))
    return 1
end
"""


class RateLimitExceeded(Exception):
    pass


async def check_rate_limit(user_id: str) -> None:
    key = f"ratelimit:{user_id}"
    now = time.time()
    member = f"{now}:{uuid.uuid4().hex[:8]}"

    allowed = await _redis.eval(
        LUA_SLIDING_WINDOW,
        1,
        key,
        str(now),
        str(settings.rate_limit_window_seconds),
        str(settings.rate_limit_requests),
        member,
    )

    if not allowed:
        raise RateLimitExceeded(
            f"Rate limit exceeded: {settings.rate_limit_requests} requests "
            f"per {settings.rate_limit_window_seconds}s"
        )

