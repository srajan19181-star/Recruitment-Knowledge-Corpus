"""
BM25 sparse retrieval.

Index is built at ingestion time and persisted to disk as safe JSON containing
the tokenized corpus, then rebuilt in memory. This eliminates arbitrary code
execution risks associated with pickle deserialization.
"""

import json
import os
import tempfile
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.config import settings
from app.models import Chunk

_bm25: BM25Okapi | None = None
_chunks: list[Chunk] = []


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _get_index_path() -> Path:
    return Path(settings.bm25_index_path)


def build_index(chunks: list[Chunk]) -> None:
    global _bm25, _chunks
    _chunks = chunks
    tokenized = [_tokenize(c.text) for c in chunks]
    _bm25 = BM25Okapi(tokenized)

    index_path = _get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)

    records = [
        {
            "chunk_id": c.chunk_id,
            "doc_id": c.doc_id,
            "page": c.page,
            "text": c.text,
            "tokens": tok,
        }
        for c, tok in zip(chunks, tokenized)
    ]

    dir_name = str(index_path.parent)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        json.dump(records, tf)
        temp_name = tf.name
    os.replace(temp_name, index_path)


def load_index() -> bool:
    global _bm25, _chunks
    index_path = _get_index_path()
    if not index_path.exists():
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    _chunks = [
        Chunk(
            chunk_id=r["chunk_id"],
            doc_id=r["doc_id"],
            page=r.get("page"),
            text=r["text"],
        )
        for r in records
    ]
    tokens = [r.get("tokens") or _tokenize(r["text"]) for r in records]
    if tokens:
        _bm25 = BM25Okapi(tokens)
    else:
        _bm25 = None
    return True


def reload_index() -> int:
    """Reloads the index from disk into memory. Returns total chunk count."""
    if load_index():
        return len(_chunks)
    return 0


def search(query: str, top_k: int | None = None) -> list[Chunk]:
    if _bm25 is None:
        if not load_index():
            return []
    top_k = top_k or settings.top_k_sparse
    tokens = _tokenize(query)
    if not tokens or _bm25 is None:
        return []
    scores = _bm25.get_scores(tokens)
    ranked = sorted(zip(_chunks, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        Chunk(chunk_id=c.chunk_id, doc_id=c.doc_id, page=c.page, text=c.text, score=float(s))
        for c, s in ranked
        if s > 0
    ]
