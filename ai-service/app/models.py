from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    user_id: str = Field(..., description="Caller identity, used for rate limiting")
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = None


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    page: Optional[int] = None
    text: str
    score: float = 0.0


class QueryDebugInfo(BaseModel):
    cache_hit: bool
    dense_hits: int
    sparse_hits: int
    fused_chunks: list[Chunk]
