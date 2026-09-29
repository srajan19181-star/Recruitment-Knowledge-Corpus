"""Shared Redis client construction, supporting both a full REDIS_URL
(managed Redis providers, e.g. Render) and discrete host/port/password
settings (local dev, docker-compose)."""

import redis.asyncio as redis

from app.config import settings


def build_redis_client() -> redis.Redis:
    if settings.redis_url:
        return redis.from_url(settings.redis_url, decode_responses=True)
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password or None,
        decode_responses=True,
    )
