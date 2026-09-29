from app.models import Chunk
from app.retrieval.fusion import reciprocal_rank_fusion


def _chunk(cid: str) -> Chunk:
    return Chunk(chunk_id=cid, doc_id="doc1", page=1, text=f"text {cid}")


def test_fusion_prefers_chunk_ranked_high_by_both():
    dense = [_chunk("a"), _chunk("b"), _chunk("c")]
    sparse = [_chunk("b"), _chunk("a"), _chunk("d")]
    fused = reciprocal_rank_fusion(dense, sparse, top_k=4)
    ids = [c.chunk_id for c in fused]
    # "a" and "b" appear near the top of both lists, so should outrank
    # "c" and "d" which only appear in one list each.
    assert set(ids[:2]) == {"a", "b"}


def test_fusion_deduplicates_by_chunk_id():
    dense = [_chunk("a"), _chunk("b")]
    sparse = [_chunk("a"), _chunk("c")]
    fused = reciprocal_rank_fusion(dense, sparse, top_k=10)
    ids = [c.chunk_id for c in fused]
    assert len(ids) == len(set(ids))


def test_fusion_respects_top_k():
    dense = [_chunk(str(i)) for i in range(10)]
    sparse = [_chunk(str(i)) for i in range(10, 20)]
    fused = reciprocal_rank_fusion(dense, sparse, top_k=5)
    assert len(fused) == 5
