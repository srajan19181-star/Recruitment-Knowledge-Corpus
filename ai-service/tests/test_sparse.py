import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import settings
from app.models import Chunk
from app.retrieval import sparse


def test_sparse_json_serialization_and_search():
    with TemporaryDirectory() as tmpdir:
        test_index_path = Path(tmpdir) / "test_bm25.json"
        original_path = settings.bm25_index_path
        settings.bm25_index_path = str(test_index_path)

        try:
            chunks = [
                Chunk(chunk_id="c1", doc_id="d1", page=1, text="Colorado Equal Pay for Equal Work Act regulations"),
                Chunk(chunk_id="c2", doc_id="d2", page=2, text="Application tracking systems and conversion funnel metrics"),
                Chunk(chunk_id="c3", doc_id="d1", page=3, text="Pay transparency range disclosure requirements for New York"),
            ]

            sparse.build_index(chunks)

            # Assert file is valid JSON and not pickle
            assert test_index_path.exists()
            with open(test_index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 3
            assert data[0]["chunk_id"] == "c1"

            # Search keyword
            hits = sparse.search("Colorado", top_k=2)
            assert len(hits) >= 1
            assert hits[0].chunk_id == "c1"

            # Test reload functionality
            count = sparse.reload_index()
            assert count == 3
        finally:
            settings.bm25_index_path = original_path
