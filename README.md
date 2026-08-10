# Production RAG Pipeline

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

A retrieval-augmented generation service built like a production system, not a notebook demo: hybrid (dense + sparse) retrieval, semantic caching with stampede protection, per-user rate limiting, token streaming, and OpenTelemetry tracing on every stage of the request path.

## Why this exists

Most RAG tutorials stop at "embed, retrieve, stuff into prompt." This project treats the infra concerns as first-class:

- **Hybrid retrieval** — dense (Qdrant) + sparse (BM25), fused with Reciprocal Rank Fusion, because a query for an error code or proper noun loses to pure embedding similarity.
- **Semantic cache** — cache key is a similarity match on the query embedding, not the raw string, with single-flight stampede protection so 100 concurrent identical questions don't trigger 100 LLM calls.
- **Rate limiting** — Redis sliding-window counter, per user.
- **Streaming** — SSE, with upstream generation cancelled on client disconnect.
- **Tracing** — a span per pipeline stage (rate limit → cache lookup → dense retrieval → sparse retrieval → fusion → prompt assembly → LLM call → stream), so latency regressions are traceable to a stage, not a guess.

## Architecture

```
Client
  │ POST /query (SSE)
  ▼
FastAPI
  ├─► Rate limiter (Redis sliding window, per user_id)
  ├─► Semantic cache lookup (embedding similarity ≥ threshold)
  │        hit  → stream cached answer
  │        miss ↓
  ├─► Retrieval
  │     ├─ Dense: Qdrant vector search
  │     └─ Sparse: BM25 over corpus
  │           → RRF fusion → top-k chunks
  ├─► Prompt assembly
  ├─► Gemini API (streaming, Flash — free tier)
  ├─► SSE tokens to client
  │        └─ on completion: write-through to semantic cache
  └─► OpenTelemetry spans wrap every stage above

Offline: PDFs → chunking → embeddings → Qdrant upsert + BM25 index build
```

## Stack

FastAPI · Qdrant · Redis · Gemini API · `sentence-transformers` (local embeddings, no extra API key) · `rank_bm25` · OpenTelemetry · Docker Compose

## Project layout

```
app/
  main.py              FastAPI app, wires everything together
  config.py            settings (env-driven)
  models.py            pydantic request/response schemas
  telemetry.py          OpenTelemetry tracer setup
  rate_limiter.py       Redis sliding-window limiter
  cache.py               semantic cache + stampede lock
  embeddings.py          embedding model wrapper
  llm.py                  Gemini streaming client
  retrieval/
    dense.py              Qdrant search
    sparse.py              BM25 index + search
    fusion.py               Reciprocal Rank Fusion
  ingestion/
    pdf_loader.py            PDF text extraction
    chunking.py               sentence-aware chunker w/ overlap
    ingest.py                  end-to-end ingestion pipeline
scripts/
  ingest_cli.py                CLI entry point for ingestion
tests/
  test_chunking.py
  test_fusion.py
docker-compose.yml
requirements.txt
```

## Setup

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` (free key: https://aistudio.google.com/apikey, no card needed).
2. `docker compose up --build` — starts Qdrant, Redis, and the API.
3. Put PDFs in `data/corpus/`, then run ingestion:
   ```bash
   docker compose exec api python scripts/ingest_cli.py --path data/corpus
   ```
4. Query:
   ```bash
   curl -N -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"user_id": "u1", "query": "What does the doc say about X?"}'
   ```
   `-N` disables curl's output buffering so you see the SSE stream token by token.

5. Open the Grafana dashboard at `http://localhost:3000` (login: `admin` / `admin`, or browse anonymously). The "RAG Pipeline" dashboard is pre-provisioned — no manual setup — showing request rate by status, cache hit rate, rate limit rejections, and p50/p95/p99 latency broken down per pipeline stage. Raw metrics are also available directly at `http://localhost:8000/metrics` and `http://localhost:9090` (Prometheus).

## Design decisions worth knowing before an interview asks about them

- **RRF over score-weighted fusion**: dense (cosine) and sparse (BM25) scores live on incomparable scales; rank position is the only thing you can fairly combine.
- **Sentence-aware chunking over fixed-token windows**: fixed windows cut mid-sentence and hurt embedding quality; the small overlap (default 20%) preserves context across chunk boundaries at controlled cost.
- **Semantic cache threshold**: default cosine ≥ 0.95 to avoid near-miss false hits returning a wrong cached answer for a subtly different question — see `app/cache.py` for where to tune this.
- **Sliding-window rate limiting over token bucket**: sliding window gives smoother burst behavior for a user-facing API; token bucket would be preferable if you wanted to allow controlled bursting (e.g., an internal batch client) — swap in `app/rate_limiter.py` if needed.

## Observability

Two complementary systems, answering different questions:

- **OpenTelemetry traces** (printed to console, or shipped via `OTEL_EXPORTER_OTLP_ENDPOINT`) — the detailed journey of *one* request through the pipeline. Good for debugging a specific slow or failed query.
- **Prometheus + Grafana** — trends *across* all requests over time: p50/p95/p99 latency per stage, cache hit rate, rate limit rejections, request rate by status. Good for answering "is this getting slower" or "is the cache actually helping," which a single trace can't tell you.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and PR to `main`:
1. **Lint** — `ruff check` against `app/` and `tests/`
2. **Unit tests** — `pytest tests/`, covering chunking and RRF fusion logic
3. **Docker build verification** — confirms the `Dockerfile` actually builds cleanly, using GitHub's build cache so it doesn't redownload torch on every run

This is a real quality gate (nothing merges to `main` with failing tests or a broken build), but it's honest to say what it *isn't*: it doesn't deploy anywhere, and there's no automated rollback or self-healing recovery — that would mean running this alongside a scheduler (e.g. Airflow) that watches production metrics and triggers a rollback action, which is a meaningfully larger project on top of this one. Framed accurately, this CI setup demonstrates you understand testing/build gates in a pipeline; it isn't a claim of production deployment automation.

## Load testing

A `locustfile.py` is not included by default — add one hitting `/query` with a mix of cached and novel queries and capture p50/p99 per pipeline stage from the traces, not just end-to-end latency.

## License

MIT
