from pathlib import Path

from app.embeddings import embed_batch
from app.ingestion.chunking import chunk_pages
from app.ingestion.pdf_loader import load_pdf
from app.models import Chunk
from app.retrieval.dense import ensure_collection, upsert_chunks
from app.retrieval.sparse import build_index


def ingest_directory(path: str, bump_version: bool = True) -> int:
    """Runs the full offline ingestion pipeline over every PDF in `path`:
    load -> chunk -> embed -> upsert to Qdrant -> rebuild BM25 index.
    Returns the number of chunks ingested.

    `bump_version` controls whether this function bumps the Redis corpus
    version itself via asyncio.run(). Set it to False when calling from
    inside an already-running event loop (e.g. FastAPI's async lifespan,
    where asyncio.run() would raise) and await bump_corpus_version()
    directly at the call site instead."""
    corpus_dir = Path(path)
    pdf_paths = sorted(corpus_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"No PDFs found in {path}")
        return 0

    all_chunks: list[Chunk] = []
    for pdf_path in pdf_paths:
        print(f"Loading {pdf_path.name}")
        pages = load_pdf(pdf_path)
        raw_chunks = chunk_pages(pages)
        for rc in raw_chunks:
            all_chunks.append(Chunk(chunk_id=rc.chunk_id, doc_id=rc.doc_id, page=rc.page, text=rc.text))
        print(f"  -> {len(raw_chunks)} chunks")

    print(f"Embedding {len(all_chunks)} chunks...")
    vectors = embed_batch([c.text for c in all_chunks])

    print("Upserting to Qdrant...")
    ensure_collection()
    upsert_chunks(all_chunks, vectors)

    print("Building BM25 index...")
    build_index(all_chunks)

    if bump_version:
        try:
            import asyncio
            from app.cache import bump_corpus_version
            asyncio.run(bump_corpus_version())
        except Exception:
            pass

    print(f"Done. Ingested {len(all_chunks)} chunks from {len(pdf_paths)} documents.")
    return len(all_chunks)
