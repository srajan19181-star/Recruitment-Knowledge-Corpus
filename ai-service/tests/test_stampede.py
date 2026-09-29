import asyncio
import pytest


@pytest.mark.asyncio
async def test_cache_stampede_single_flight_calls_llm_once():
    """Simulates 5 concurrent identical requests.
    Verifies that the single-flight lock + immediate cache re-check
    guarantees the LLM generation is invoked exactly once.
    """
    cache_store = {}
    lock = asyncio.Lock()
    llm_call_count = 0

    async def mock_lookup(query: str):
        return cache_store.get(query)

    async def mock_write(query: str, answer: str):
        cache_store[query] = answer

    async def mock_llm_call(query: str) -> str:
        nonlocal llm_call_count
        llm_call_count += 1
        # Simulate realistic generation latency
        await asyncio.sleep(0.05)
        return f"Generated answer for {query}"

    async def execute_request(query: str):
        # 1. Initial cache check
        cached = await mock_lookup(query)
        if cached:
            return cached

        # 2. Acquire single-flight lock
        async with lock:
            # Crucial stampede re-check: look up again immediately after acquiring lock
            recheck = await mock_lookup(query)
            if recheck is not None:
                return recheck

            # 3. Only the winning caller computes
            computed = await mock_llm_call(query)
            await mock_write(query, computed)
            return computed

    query = "What are NYC pay transparency salary rules?"

    # Launch 5 identical concurrent requests
    results = await asyncio.gather(*(execute_request(query) for _ in range(5)))

    # All 5 requests received the valid answer
    assert len(results) == 5
    for res in results:
        assert res == f"Generated answer for {query}"

    # LLM was invoked strictly once
    assert llm_call_count == 1
