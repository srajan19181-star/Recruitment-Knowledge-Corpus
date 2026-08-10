"""
Prometheus metrics for the RAG pipeline. These are distinct from the
OpenTelemetry traces in telemetry.py: traces show you one request's
journey through the pipeline in detail; these metrics show you trends
across all requests over time (p99 latency, cache hit rate, etc.) —
which is what Prometheus/Grafana are actually good at answering.
"""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total number of /query requests",
    ["status"],  # "success" | "error" | "rate_limited"
)

STAGE_LATENCY = Histogram(
    "rag_stage_latency_seconds",
    "Latency of each pipeline stage",
    ["stage"],  # "rate_limit" | "cache_lookup" | "dense_search" | "sparse_search" | "fusion" | "llm_call"
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

CACHE_HITS = Counter("rag_cache_hits_total", "Semantic cache hits")
CACHE_MISSES = Counter("rag_cache_misses_total", "Semantic cache misses")

RATE_LIMIT_REJECTIONS = Counter(
    "rag_rate_limit_rejections_total", "Requests rejected by the rate limiter"
)

CHUNKS_RETRIEVED = Histogram(
    "rag_chunks_retrieved",
    "Number of chunks used in the final fused context",
    buckets=(0, 1, 2, 3, 5, 7, 10, 15, 20),
)
