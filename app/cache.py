"""
Semantic cache: the cache key is a similarity match on the query
embedding against previously-answered queries, not the raw query string.

Two failure modes this is designed around:

1. Near-miss false hits — a query embedding just below the similarity
   threshold could return a wrong cached answer for a subtly different
   question. CACHE_SIMILARITY_THRESHOLD defaults conservatively high
   (0.95); tune with an eval set before lowering it.

2. Cache stampede — many concurrent requests for the same novel query
   would otherwise all miss the cache and all hit the LLM. A Redis lock
   (single-flight) makes only the first caller compute the answer; the
   rest wait on the lock and then read the freshly-written cache entry.
"""

import asyncio
import hashlib
import json
import time

import redis.asyncio as redis

from app.config import settings
from app.embeddings import cosine_similarity, embed

_redis = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

CACHE_INDEX_KEY = "semcache:index"  # hash of query_hash -> {embedding, answer, ts}
LOCK_TTL_SECONDS = 30
LOCK_POLL_INTERVAL = 0.2
LOCK_MAX_WAIT = 20


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def lookup(query: str) -> str | None:
    """Return a cached answer if a sufficiently similar query was answered before."""
    query_vec = embed(query)
    entries = await _redis.hgetall(CACHE_INDEX_KEY)

    best_score, best_answer = 0.0, None
    now = time.time()
    for raw in entries.values():
        entry = json.loads(raw)
        if now - entry["ts"] > settings.cache_ttl_seconds:
            continue
        score = cosine_similarity(query_vec, entry["embedding"])
        if score > best_score:
            best_score, best_answer = score, entry["answer"]

    if best_score >= settings.cache_similarity_threshold:
        return best_answer
    return None


async def write(query: str, answer: str) -> None:
    query_vec = embed(query)
    entry = json.dumps({"embedding": query_vec, "answer": answer, "ts": time.time()})
    await _redis.hset(CACHE_INDEX_KEY, _hash(query), entry)


class CacheLock:
    """
    Single-flight lock keyed by query hash. Use as:

        async with CacheLock(query) as acquired:
            if acquired:
                # this caller computes the answer and writes the cache
                ...
            else:
                # another caller is already computing it; re-check cache
                answer = await lookup(query)
    """

    def __init__(self, query: str):
        self.key = f"semcache:lock:{_hash(query)}"
        self.acquired = False

    async def __aenter__(self) -> bool:
        waited = 0.0
        while waited < LOCK_MAX_WAIT:
            self.acquired = await _redis.set(self.key, "1", nx=True, ex=LOCK_TTL_SECONDS)
            if self.acquired:
                return True
            await asyncio.sleep(LOCK_POLL_INTERVAL)
            waited += LOCK_POLL_INTERVAL
        return False  # gave up waiting; caller should compute anyway

    async def __aexit__(self, *exc):
        if self.acquired:
            await _redis.delete(self.key)
