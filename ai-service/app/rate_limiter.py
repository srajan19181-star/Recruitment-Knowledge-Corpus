"""
Sliding-window rate limiter backed by Redis sorted sets.

Why sliding window over token bucket: a user-facing query endpoint should
have smooth, predictable throttling rather than allow bursts up to bucket
capacity. Token bucket is the better choice if you want to intentionally
allow controlled bursting (e.g. a trusted internal batch client) — that
trade-off is the actual thing to be able to explain, not just "I rate
limited it."

Algorithm: for key `user_id`, store request timestamps in a sorted set.
On each request: drop entries older than `window_seconds`, count what's
left, reject if >= limit, else add the current timestamp.
"""

import time

import redis.asyncio as redis

from app.config import settings

_redis = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


class RateLimitExceeded(Exception):
    pass


async def check_rate_limit(user_id: str) -> None:
    key = f"ratelimit:{user_id}"
    now = time.time()
    window_start = now - settings.rate_limit_window_seconds

    await _redis.zremrangebyscore(key, 0, window_start)
    count = await _redis.zcard(key)

    if count >= settings.rate_limit_requests:
        raise RateLimitExceeded(
            f"Rate limit exceeded: {settings.rate_limit_requests} requests "
            f"per {settings.rate_limit_window_seconds}s"
        )

    async with _redis.pipeline(transaction=True) as pipe:
        pipe.zadd(key, {f"{now}:{id(now)}": now})
        pipe.expire(key, settings.rate_limit_window_seconds)
        await pipe.execute()
