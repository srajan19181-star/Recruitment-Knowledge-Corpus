"""
Thin wrapper around the Gemini streaming API. Yields text deltas as they
arrive so the FastAPI layer can forward them over SSE without buffering
the full response.

Uses Gemini because Flash / Flash-Lite have a genuine free tier (no
credit card, generous daily request quota) — good enough for a portfolio
project's generation step, which doesn't need frontier-level reasoning
over a handful of retrieved chunks. Swap the model name in .env if you
want to test against Pro or a different provider later; the streaming
interface below (`stream_answer`) is what the rest of the pipeline
depends on, so a provider swap only touches this file.
"""

from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from app.config import settings
from app.models import Chunk

_client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions using only the provided "
    "context. If the context doesn't contain the answer, say so directly "
    "instead of guessing. Cite which source chunk (by chunk_id) supports "
    "each claim where possible."
)


def build_prompt(query: str, chunks: list[Chunk]) -> str:
    context = "\n\n".join(f"[{c.chunk_id}] (doc={c.doc_id}, page={c.page})\n{c.text}" for c in chunks)
    return f"Context:\n{context}\n\nQuestion: {query}"


async def stream_answer(query: str, chunks: list[Chunk]) -> AsyncIterator[str]:
    prompt = build_prompt(query, chunks)
    stream = await _client.aio.models.generate_content_stream(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024,
        ),
    )
    async for chunk in stream:
        if chunk.text:
            yield chunk.text
