"""
Sentence-aware chunking with overlap, over two alternatives worth being
able to compare in an interview:

- Fixed-token windows: simplest, but cuts mid-sentence and hurts
  embedding quality since a chunk can start/end on a sentence fragment.
- Full semantic chunking (embed sentences, split on similarity drops):
  best coherence, but adds an embedding call per sentence at ingestion
  time — meaningful cost at scale for marginal gain over sentence-aware
  splitting on most corpora.

This implementation: split into sentences, then greedily pack sentences
into chunks up to CHUNK_SIZE_TOKENS (approximated by whitespace-split
word count — good enough without pulling in a tokenizer), carrying the
last CHUNK_OVERLAP_RATIO fraction of a chunk's sentences into the next
chunk so context isn't lost at boundaries.
"""

import hashlib
import re
import uuid
from dataclasses import dataclass

from app.config import settings
from app.ingestion.pdf_loader import PageText

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class RawChunk:
    chunk_id: str
    doc_id: str
    page: int
    text: str


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_pages(pages: list[PageText]) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    max_words = settings.chunk_size_tokens
    overlap_ratio = settings.chunk_overlap_ratio

    for page in pages:
        sentences = _split_sentences(page.text)
        current: list[str] = []
        current_words = 0

        for sentence in sentences:
            sentence_words = _word_count(sentence)
            if current and current_words + sentence_words > max_words:
                chunks.append(_make_chunk(page.doc_id, page.page, current))
                overlap_count = max(1, int(len(current) * overlap_ratio))
                current = current[-overlap_count:]
                current_words = sum(_word_count(s) for s in current)

            current.append(sentence)
            current_words += sentence_words

        if current:
            chunks.append(_make_chunk(page.doc_id, page.page, current))

    return chunks


def _make_chunk(doc_id: str, page: int, sentences: list[str]) -> RawChunk:
    text = " ".join(sentences)
    # Deterministic ID (not random) so re-ingesting the same doc upserts
    # in place instead of duplicating chunks in Qdrant.
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{page}:{text_hash}"))
    return RawChunk(chunk_id=chunk_id, doc_id=doc_id, page=page, text=text)
