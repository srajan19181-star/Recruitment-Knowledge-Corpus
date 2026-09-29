from pathlib import Path
from app.ingestion.chunking import chunk_pages
from app.ingestion.pdf_loader import load_pdf


def test_recruitment_corpus_loads_and_chunks():
    corpus_dir = Path("data/corpus")
    pdf_files = list(corpus_dir.glob("*.pdf"))

    assert len(pdf_files) == 10, f"Expected 10 PDFs, found {len(pdf_files)}"

    for pdf_path in pdf_files:
        pages = load_pdf(pdf_path)
        assert len(pages) >= 2, f"{pdf_path.name} should have at least 2 pages"

        chunks = chunk_pages(pages)
        assert len(chunks) >= 2, f"{pdf_path.name} should yield at least 2 chunks"

        for c in chunks:
            assert c.doc_id == pdf_path.stem
            assert len(c.text.strip()) > 0
            assert c.page in [1, 2]
