from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "rag_chunks"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Retrieval
    top_k_dense: int = 10
    top_k_sparse: int = 10
    top_k_final: int = 5
    rrf_k: int = 60

    # Semantic cache
    cache_similarity_threshold: float = 0.95
    cache_ttl_seconds: int = 3600

    # Rate limiting
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    # Chunking
    chunk_size_tokens: int = 300
    chunk_overlap_ratio: float = 0.2

    # Telemetry
    otel_exporter_otlp_endpoint: str = ""


settings = Settings()
