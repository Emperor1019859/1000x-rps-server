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
        await asyncio.sleep(0.01)  # Small sleep to ensure overlap
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
async def test_queue_10_users(mock_kafka):
    """Happy flow: 10 concurrent users should all get gift codes."""
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.get("/queue") for _ in range(10)]
        responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert data["gift_code"] == "MOCK-GIFT-CODE"
        assert "request_id" in data


@pytest.mark.asyncio
async def test_queue_100_users(mock_kafka):
    """At capacity: 100 concurrent users should all get gift codes."""
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.get("/queue") for _ in range(100)]
        responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 100

    for resp in responses:
        if resp.status_code == 200:
            assert resp.json()["gift_code"] == "MOCK-GIFT-CODE"


@pytest.mark.asyncio
async def test_queue_500_users(mock_kafka):
    """Overload: 500 concurrent users. Only 100 should succeed, 400 should get 429."""
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as ac:
        tasks = [ac.get("/queue") for _ in range(500)]
        responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)

    print(f"Success: {success_count}, Rate Limited: {rate_limited_count}")

    # Given the capacity is 100 and we have a 0.01s sleep in the mock,
    # 500 simultaneous requests should hit the limit correctly.
    assert success_count == 100
    assert rate_limited_count == 400
