"""
Semantic cache: query embedding similarity matching backed by Qdrant.

Design considerations:
1. Qdrant-backed similarity search: avoids pulling all cache entries into Python memory
   and computing cosine similarities in the event loop.
2. TTL & Expiration: points carry an `expires_at` payload timestamp, filtered out
   at query time via Qdrant payload filters.
3. Corpus versioning: each cache entry records `corpus_version`. Whenever new documents
   are ingested, the version counter in Redis is bumped so stale answers are invalidated.
4. Single-flight lock (CacheLock): prevents cache stampede when multiple concurrent callers
   ask the same novel question.
"""

import asyncio
import hashlib
import time
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.embeddings import embed
from app.redis_client import build_redis_client

_redis = build_redis_client()

CORPUS_VERSION_KEY = "rag:corpus_version"
LOCK_TTL_SECONDS = 30
LOCK_POLL_INTERVAL = 0.15
LOCK_MAX_WAIT = 15.0


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key or None,
        https=settings.qdrant_https,
    )


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_cache_collection() -> None:
    client = _get_qdrant_client()
    try:
        existing = [c.name for c in client.get_collections().collections]
        if settings.qdrant_cache_collection not in existing:
            client.create_collection(
                collection_name=settings.qdrant_cache_collection,
                vectors_config=qmodels.VectorParams(
                    size=settings.embedding_dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
    except Exception:
        # Client might not be ready during certain offline unit tests
        pass


async def get_corpus_version() -> int:
    try:
        val = await _redis.get(CORPUS_VERSION_KEY)
        return int(val) if val is not None else 1
    except Exception:
        return 1


async def bump_corpus_version() -> int:
    try:
        return await _redis.incr(CORPUS_VERSION_KEY)
    except Exception:
        return 1


async def lookup(query: str) -> str | None:
    """Return a cached answer if a sufficiently similar query was answered before
    for the current corpus version and has not expired."""
    query_vec = embed(query)
    current_version = await get_corpus_version()
    now = time.time()

    query_filter = qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="corpus_version",
                match=qmodels.MatchValue(value=current_version),
            ),
            qmodels.FieldCondition(
                key="expires_at",
                range=qmodels.Range(gt=now),
            ),
        ]
    )

    try:
        client = _get_qdrant_client()
        hits = client.search(
            collection_name=settings.qdrant_cache_collection,
            query_vector=query_vec,
            query_filter=query_filter,
            limit=1,
        )
        if hits and hits[0].score >= settings.cache_similarity_threshold:
            return hits[0].payload.get("answer")
    except Exception:
        return None

    return None


async def write(query: str, answer: str) -> None:
    """Persist query embedding and answer with expiration and corpus version."""
    query_vec = embed(query)
    current_version = await get_corpus_version()
    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"cache:{query}"))

    point = qmodels.PointStruct(
        id=point_id,
        vector=query_vec,
        payload={
            "query": query,
            "answer": answer,
            "expires_at": time.time() + settings.cache_ttl_seconds,
            "corpus_version": current_version,
        },
    )

    try:
        client = _get_qdrant_client()
        client.upsert(collection_name=settings.qdrant_cache_collection, points=[point])
    except Exception:
        pass


def cleanup_expired() -> None:
    """Prunes expired cache entries from Qdrant."""
    try:
        client = _get_qdrant_client()
        now = time.time()
        client.delete(
            collection_name=settings.qdrant_cache_collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="expires_at",
                            range=qmodels.Range(lt=now),
                        )
                    ]
                )
            ),
        )
    except Exception:
        pass


class CacheLock:
    """
    Single-flight lock keyed by query hash. Ensures only the first caller computes
    the answer, while concurrent callers wait and then re-read the cache.
    """

    def __init__(self, query: str):
        self.key = f"semcache:lock:{_hash(query)}"
        self.acquired = False

    async def __aenter__(self) -> bool:
        waited = 0.0
        while waited < LOCK_MAX_WAIT:
            try:
                self.acquired = bool(await _redis.set(self.key, "1", nx=True, ex=LOCK_TTL_SECONDS))
                if self.acquired:
                    return True
            except Exception:
                return True
            await asyncio.sleep(LOCK_POLL_INTERVAL)
            waited += LOCK_POLL_INTERVAL
        return False

    async def __aexit__(self, *exc):
        if self.acquired:
            try:
                await _redis.delete(self.key)
            except Exception:
                pass

