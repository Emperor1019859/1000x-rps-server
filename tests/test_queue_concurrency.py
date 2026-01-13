import asyncio
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

import main
from core.config import settings
from core.security import RateLimiter


@pytest.fixture(autouse=True)
async def setup_dependencies():
    """Re-initialize dependencies to ensure they use the test event loop."""
    # Re-initialize RateLimiter to avoid event loop mismatch
    old_limiter = main.rate_limiter
    main.rate_limiter = RateLimiter(redis_url=settings.REDIS_URL, capacity=settings.RATE_LIMIT_CAPACITY)

    # Clear Redis
    await main.rate_limiter.redis.delete(main.rate_limiter.key)

    yield

    # Cleanup
    await main.rate_limiter.redis.delete(main.rate_limiter.key)
    # Ensure redis connection is closed
    await main.rate_limiter.redis.aclose()
    main.rate_limiter = old_limiter


@pytest.fixture
def mock_kafka():
    """Mock Kafka to simulate successful gift code retrieval."""
    # Ensure producer/consumer check passes
    main.kafka_manager.producer = MagicMock()
    main.kafka_manager.consumer = MagicMock()

    async def slow_get_gift_code(*args, **kwargs):
        await asyncio.sleep(0.1)  # Small sleep to ensure overlap
        return "MOCK-GIFT-CODE"

    # Mock the response
    original_get_gift_code = main.kafka_manager.get_gift_code
    main.kafka_manager.get_gift_code = MagicMock(side_effect=slow_get_gift_code)

    yield main.kafka_manager

    # Restore
    main.kafka_manager.producer = None
    main.kafka_manager.consumer = None
    main.kafka_manager.get_gift_code = original_get_gift_code


@pytest.mark.asyncio
async def test_queue_small_batch(mock_kafka):
    """Happy flow: A small number of concurrent users should all get gift codes."""
    num_users = min(10, settings.RATE_LIMIT_CAPACITY)
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.post("/queue") for _ in range(num_users)]
        responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert data["gift_code"] == "MOCK-GIFT-CODE"
        assert "request_id" in data


@pytest.mark.asyncio
async def test_queue_at_capacity(mock_kafka):
    """At capacity: users up to RATE_LIMIT_CAPACITY should all get gift codes."""
    num_users = settings.RATE_LIMIT_CAPACITY
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.post("/queue") for _ in range(num_users)]
        responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == num_users

    for resp in responses:
        if resp.status_code == 200:
            assert resp.json()["gift_code"] == "MOCK-GIFT-CODE"


@pytest.mark.asyncio
async def test_queue_overload(mock_kafka):
    """Overload: More users than RATE_LIMIT_CAPACITY. Only RATE_LIMIT_CAPACITY should succeed."""
    capacity = settings.RATE_LIMIT_CAPACITY
    num_users = capacity * 5
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.post("/queue") for _ in range(num_users)]
        responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)

    print(f"Success: {success_count}, Rate Limited: {rate_limited_count}")

    # Given the capacity is settings.RATE_LIMIT_CAPACITY
    assert success_count == capacity
    assert rate_limited_count == num_users - capacity
