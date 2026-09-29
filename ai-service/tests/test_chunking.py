from app.ingestion.chunking import chunk_pages
from app.ingestion.pdf_loader import PageText


def test_chunking_produces_deterministic_ids():
    page = PageText(doc_id="doc1", page=1, text="Sentence one. Sentence two. Sentence three.")
    chunks_a = chunk_pages([page])
    chunks_b = chunk_pages([page])
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]


def test_chunking_respects_max_words():
    long_text = " ".join(f"Word{i} sentence number {i}." for i in range(200))
    page = PageText(doc_id="doc1", page=1, text=long_text)
    chunks = chunk_pages([page])
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text.split()) <= 400  # allows headroom for the last sentence


def test_chunk_overlap_carries_context():
    page = PageText(
        doc_id="doc1",
        page=1,
        text=" ".join(f"This is sentence number {i} in the document." for i in range(60)),
    )
    chunks = chunk_pages([page])
    assert len(chunks) > 1
    # Overlap means consecutive chunks should share at least one sentence.
    first_sentences = set(chunks[0].text.split(". "))
    second_sentences = set(chunks[1].text.split(". "))
    assert first_sentences & second_sentences
