from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.embeddings import embed
from app.models import Chunk

_client = QdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
    api_key=settings.qdrant_api_key or None,
    https=settings.qdrant_https,
)


def ensure_collection() -> None:
    existing = [c.name for c in _client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        _client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(
                size=settings.embedding_dim,
                distance=qmodels.Distance.COSINE,
            ),
        )


def upsert_chunks(chunks: list[Chunk], vectors: list[list[float]]) -> None:
    points = [
        qmodels.PointStruct(
            id=c.chunk_id,
            vector=vec,
            payload={"doc_id": c.doc_id, "page": c.page, "text": c.text},
        )
        for c, vec in zip(chunks, vectors)
    ]
    _client.upsert(collection_name=settings.qdrant_collection, points=points)


def search(query: str, top_k: int | None = None) -> list[Chunk]:
    top_k = top_k or settings.top_k_dense
    query_vec = embed(query)
    hits = _client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vec,
        limit=top_k,
    )
    return [
        Chunk(
            chunk_id=str(h.id),
            doc_id=h.payload["doc_id"],
            page=h.payload.get("page"),
            text=h.payload["text"],
            score=h.score,
        )
        for h in hits
    ]
