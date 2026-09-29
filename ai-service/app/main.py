import asyncio
import json
import time
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sse_starlette.sse import EventSourceResponse

from app import cache
from app.llm import stream_answer
from app.metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CHUNKS_RETRIEVED,
    RATE_LIMIT_REJECTIONS,
    REQUEST_COUNT,
    STAGE_LATENCY,
)
from app.models import QueryRequest
from app.rate_limiter import RateLimitExceeded, check_rate_limit
from app.retrieval import dense, sparse
from app.retrieval.fusion import reciprocal_rank_fusion
from app.telemetry import tracer

app = FastAPI(title="Production RAG Pipeline")
FastAPIInstrumentor.instrument_app(app)


@contextmanager
def timed_stage(name: str):
    """Wraps a pipeline stage in both an OpenTelemetry span (for per-request
    tracing) and a Prometheus histogram observation (for trends across
    requests) — the two systems answer different questions, so both stay."""
    start = time.perf_counter()
    with tracer.start_as_current_span(name):
        yield
    STAGE_LATENCY.labels(stage=name).observe(time.perf_counter() - start)


@app.on_event("startup")
async def startup() -> None:
    dense.ensure_collection()
    sparse.load_index()  # no-op if nothing ingested yet


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/query")
async def query(req: QueryRequest, request: Request):
    with timed_stage("rate_limit"):
        try:
            await check_rate_limit(req.user_id)
        except RateLimitExceeded as e:
            RATE_LIMIT_REJECTIONS.inc()
            REQUEST_COUNT.labels(status="rate_limited").inc()
            raise HTTPException(status_code=429, detail=str(e))

    with timed_stage("cache_lookup"):
        cached = await cache.lookup(req.query)

    if cached is not None:
        CACHE_HITS.inc()
        REQUEST_COUNT.labels(status="success").inc()
        return EventSourceResponse(_replay_cached(cached))

    CACHE_MISSES.inc()

    async def event_stream():
        async with cache.CacheLock(req.query) as acquired:
            if not acquired:
                # Another request is already computing this answer.
                # Re-check the cache once more before falling through to
                # computing it ourselves (better a duplicate LLM call than
                # an indefinite wait).
                recheck = await cache.lookup(req.query)
                if recheck is not None:
                    CACHE_HITS.inc()
                    async for chunk in _replay_cached(recheck):
                        yield chunk
                    return

            with timed_stage("retrieval"):
                # Dense and sparse retrieval don't depend on each other, so
                # run them concurrently instead of sequentially — each is a
                # blocking network call, so to_thread keeps the event loop
                # free while both are in flight.
                dense_start = time.perf_counter()
                dense_hits, sparse_hits = await asyncio.gather(
                    asyncio.to_thread(dense.search, req.query, req.top_k),
                    asyncio.to_thread(sparse.search, req.query, req.top_k),
                )
                STAGE_LATENCY.labels(stage="dense_search").observe(
                    time.perf_counter() - dense_start
                )

                with timed_stage("fusion"):
                    fused = reciprocal_rank_fusion(dense_hits, sparse_hits, top_k=req.top_k)
                CHUNKS_RETRIEVED.observe(len(fused))

            full_answer = []
            llm_start = time.perf_counter()
            try:
                with tracer.start_as_current_span("llm_call"):
                    async for delta in stream_answer(req.query, fused):
                        if await request.is_disconnected():
                            # Client hung up mid-stream — stop pulling more
                            # tokens from the upstream generation instead of
                            # burning tokens/latency for no one.
                            REQUEST_COUNT.labels(status="error").inc()
                            return
                        full_answer.append(delta)
                        yield {"event": "token", "data": delta}
            except asyncio.CancelledError:
                REQUEST_COUNT.labels(status="error").inc()
                return
            finally:
                STAGE_LATENCY.labels(stage="llm_call").observe(time.perf_counter() - llm_start)

            answer_text = "".join(full_answer)
            with timed_stage("cache_write"):
                await cache.write(req.query, answer_text)

            REQUEST_COUNT.labels(status="success").inc()
            yield {"event": "done", "data": json.dumps({"chunks_used": len(fused)})}

    return EventSourceResponse(event_stream())


async def _replay_cached(answer: str):
    yield {"event": "token", "data": answer}
    yield {"event": "done", "data": json.dumps({"cache_hit": True})}
