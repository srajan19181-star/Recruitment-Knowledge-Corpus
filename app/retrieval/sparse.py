"""
BM25 sparse retrieval. Qdrant handles the dense side; BM25 catches exact
keyword/entity matches (error codes, proper nouns) that dense embedding
similarity tends to miss.

Index is built at ingestion time and persisted to disk as a pickle next
to the corpus, then loaded once at API startup. For a corpus large enough
that this becomes a problem, swap in Qdrant's sparse-vector support or
an OpenSearch/Elasticsearch BM25 index instead of this in-memory version.
"""

import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.config import settings
from app.models import Chunk

_INDEX_PATH = Path("data/bm25_index.pkl")

_bm25: BM25Okapi | None = None
_chunks: list[Chunk] = []


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_index(chunks: list[Chunk]) -> None:
    global _bm25, _chunks
    _chunks = chunks
    tokenized = [_tokenize(c.text) for c in chunks]
    _bm25 = BM25Okapi(tokenized)
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": _bm25, "chunks": _chunks}, f)


def load_index() -> bool:
    global _bm25, _chunks
    if not _INDEX_PATH.exists():
        return False
    with open(_INDEX_PATH, "rb") as f:
        data = pickle.load(f)
    _bm25, _chunks = data["bm25"], data["chunks"]
    return True


def search(query: str, top_k: int | None = None) -> list[Chunk]:
    if _bm25 is None:
        if not load_index():
            return []
    top_k = top_k or settings.top_k_sparse
    scores = _bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(_chunks, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        Chunk(chunk_id=c.chunk_id, doc_id=c.doc_id, page=c.page, text=c.text, score=float(s))
        for c, s in ranked
        if s > 0
    ]
