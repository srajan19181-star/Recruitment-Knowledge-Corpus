import asyncio
from contextlib import asynccontextmanager, contextmanager
import json
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sse_starlette.sse import EventSourceResponse

from app import cache
from app.config import settings
from app.ingestion.ingest import ingest_directory
from app.llm import stream_answer, validate_gemini_model
from app.metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CHUNKS_RETRIEVED,
    LLM_ERRORS,
    RATE_LIMIT_REJECTIONS,
    REQUEST_COUNT,
    STAGE_LATENCY,
)
from app.models import QueryRequest
from app.rate_limiter import RateLimitExceeded, check_rate_limit
from app.retrieval import dense, sparse
from app.retrieval.fusion import reciprocal_rank_fusion
from app.telemetry import tracer
from app.tools import check_ad_compliance, draft_job_ad


@contextmanager
def timed_stage(name: str):
    """Wraps a pipeline stage in both an OpenTelemetry span and a Prometheus histogram."""
    start = time.perf_counter()
    with tracer.start_as_current_span(name):
        yield
    STAGE_LATENCY.labels(stage=name).observe(time.perf_counter() - start)


CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "corpus"


async def _background_startup_tasks() -> None:
    """Runs the slow, non-critical startup work (corpus ingestion, Gemini
    model validation) after the app is already accepting connections, so a
    slow embedding-model load or a live Gemini API round-trip can never
    block uvicorn from binding its port - which platforms like Render treat
    as a deploy failure ("No open ports detected") if it takes too long."""
    if CORPUS_DIR.exists() and any(CORPUS_DIR.glob("*.pdf")):
        try:
            await asyncio.to_thread(ingest_directory, str(CORPUS_DIR), False)
            await cache.bump_corpus_version()
        except Exception as e:
            print(f"Startup corpus ingestion failed (continuing with existing index): {e}")

    if settings.llm_provider == "gemini":
        try:
            await validate_gemini_model()
        except Exception as e:
            print(f"Gemini model validation failed (will surface again on first real query): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence - kept fast so the port opens immediately.
    dense.ensure_collection()
    cache.ensure_cache_collection()
    sparse.load_index()

    asyncio.create_task(_background_startup_tasks())

    yield
    # Shutdown sequence


app = FastAPI(title="Recruiter Assistant AI Service", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)


def _validate_internal_auth(request: Request) -> None:
    if not settings.internal_api_key:
        return
    provided = request.headers.get("x-internal-api-key")
    if provided != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized internal call")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.gemini_model,
    }


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/retrieval/reload")
async def reload_retrieval(request: Request) -> dict:
    _validate_internal_auth(request)
    count = sparse.reload_index()
    await cache.bump_corpus_version()
    return {"status": "ok", "chunks_indexed": count}


@app.post("/tools/check-compliance")
async def check_compliance(payload: dict, request: Request) -> dict:
    _validate_internal_auth(request)
    ad_text = payload.get("ad_text", "")
    jurisdiction = payload.get("jurisdiction", "")
    return check_ad_compliance(ad_text, jurisdiction)


@app.post("/tools/draft-ad")
async def draft_ad(payload: dict, request: Request) -> dict:
    _validate_internal_auth(request)
    return draft_job_ad(
        role=payload.get("role", "Software Engineer"),
        level=payload.get("level", "Mid-Level"),
        location=payload.get("location", "Remote"),
        salary_range=payload.get("salary_range", "$120,000 - $150,000"),
        must_haves=payload.get("must_haves", []),
    )


@app.post("/query")
async def query(req: QueryRequest, request: Request):
    _validate_internal_auth(request)

    # Use trusted header set by the gateway; fallback to body if testing directly
    user_id = request.headers.get("x-user-id") or req.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing required X-User-Id header")

    with timed_stage("rate_limit"):
        try:
            await check_rate_limit(user_id)
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
        async with cache.CacheLock(req.query):
            # Re-check the semantic cache immediately after acquiring lock.
            # If another request just finished computing while we were waiting,
            # we return the freshly cached answer rather than duplicating LLM compute.
            recheck = await cache.lookup(req.query)
            if recheck is not None:
                CACHE_HITS.inc()
                REQUEST_COUNT.labels(status="success").inc()
                async for chunk in _replay_cached(recheck):
                    yield chunk
                return

            with timed_stage("retrieval"):
                async def _timed_dense():
                    t0 = time.perf_counter()
                    res = await asyncio.to_thread(dense.search, req.query, req.top_k)
                    STAGE_LATENCY.labels(stage="dense_search").observe(time.perf_counter() - t0)
                    return res

                async def _timed_sparse():
                    t0 = time.perf_counter()
                    res = await asyncio.to_thread(sparse.search, req.query, req.top_k)
                    STAGE_LATENCY.labels(stage="sparse_search").observe(time.perf_counter() - t0)
                    return res

                dense_hits, sparse_hits = await asyncio.gather(_timed_dense(), _timed_sparse())

                with timed_stage("fusion"):
                    fused = reciprocal_rank_fusion(dense_hits, sparse_hits, top_k=req.top_k)
                CHUNKS_RETRIEVED.observe(len(fused))

            full_answer = []
            llm_start = time.perf_counter()
            try:
                with tracer.start_as_current_span("llm_call"):
                    async for delta in stream_answer(req.query, fused):
                        if await request.is_disconnected():
                            REQUEST_COUNT.labels(status="error").inc()
                            return
                        full_answer.append(delta)
                        yield {"event": "token", "data": delta}
            except asyncio.CancelledError:
                REQUEST_COUNT.labels(status="error").inc()
                return
            except Exception as e:
                LLM_ERRORS.inc()
                REQUEST_COUNT.labels(status="error").inc()
                yield {"event": "error", "data": json.dumps({"error": f"LLM generation failed: {str(e)}"})}
                return
            finally:
                STAGE_LATENCY.labels(stage="llm_call").observe(time.perf_counter() - llm_start)

            answer_text = "".join(full_answer)
            with timed_stage("cache_write"):
                await cache.write(req.query, answer_text)

            REQUEST_COUNT.labels(status="success").inc()
            citations = [{"chunk_id": c.chunk_id, "doc_id": c.doc_id, "page": c.page} for c in fused]
            yield {
                "event": "done",
                "data": json.dumps({"chunks_used": len(fused), "citations": citations}),
            }

    return EventSourceResponse(event_stream())


async def _replay_cached(answer: str):
    yield {"event": "token", "data": answer}
    yield {"event": "done", "data": json.dumps({"cache_hit": True})}
