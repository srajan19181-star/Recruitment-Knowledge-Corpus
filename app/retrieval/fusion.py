"""
Reciprocal Rank Fusion (RRF).

Dense (cosine similarity) and sparse (BM25) scores live on incomparable
scales, so blending them with weights is arbitrary. RRF instead combines
*rank position*, which is directly comparable across retrievers:

    RRF_score(chunk) = sum over retrievers of 1 / (k + rank)

`k` (default 60, per the original RRF paper) dampens the influence of
any single very-high rank so one retriever can't dominate the fused
ranking just by putting something first.
"""

from app.config import settings
from app.models import Chunk


def reciprocal_rank_fusion(
    dense_results: list[Chunk],
    sparse_results: list[Chunk],
    top_k: int | None = None,
    k: int | None = None,
) -> list[Chunk]:
    k = k or settings.rrf_k
    top_k = top_k or settings.top_k_final

    scores: dict[str, float] = {}
    chunk_lookup: dict[str, Chunk] = {}

    for rank, chunk in enumerate(dense_results, start=1):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
        chunk_lookup[chunk.chunk_id] = chunk

    for rank, chunk in enumerate(sparse_results, start=1):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
        chunk_lookup.setdefault(chunk.chunk_id, chunk)

    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_k]

    fused = []
    for cid in ranked_ids:
        chunk = chunk_lookup[cid]
        fused.append(chunk.model_copy(update={"score": scores[cid]}))
    return fused
