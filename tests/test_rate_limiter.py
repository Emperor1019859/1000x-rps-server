import asyncio

import pytest

from core.config import settings
from core.security import RateLimiter


@pytest.fixture
async def rate_limiter():
    """Fixture to provide a RateLimiter instance connected to the test Redis."""
    # Use settings.REDIS_URL which should point to localhost:6379 for local tests
    limiter = RateLimiter(redis_url=settings.REDIS_URL, capacity=5)
    # Clear the test key before each test
    await limiter.redis.delete(limiter.key)
    yield limiter
    # Cleanup after test
    await limiter.redis.delete(limiter.key)


@pytest.mark.asyncio
async def test_validate_success(rate_limiter):
    """Test successful acquisition of a slot."""
    success = await rate_limiter.validate()
    assert success is True

    # Verify count
    count = await rate_limiter.redis.get(rate_limiter.key)
    assert int(count) == 1


@pytest.mark.asyncio
async def test_validate_capacity_exceeded(rate_limiter):
    """Test that acquisition fails when capacity is reached."""
    # Fill up the capacity (capacity is 5 in the fixture)
    for _ in range(5):
        await rate_limiter.validate()

    # Try to validate one more
    success = await rate_limiter.validate()
    assert success is False

    # Verify count is still at capacity
    count = await rate_limiter.redis.get(rate_limiter.key)
    assert int(count) == 5


@pytest.mark.asyncio
async def test_release(rate_limiter):
    """Test releasing a slot."""
    await rate_limiter.validate()

    # Release it
    await rate_limiter.release()

    # Verify count is 0
    count = await rate_limiter.redis.get(rate_limiter.key)
    # redis returns None if key doesn't exist, or 0 if we decr to 0?
    # Actually if we INCR then DECR, it might be "0" string.
    # If we DECR a non-existent key, it becomes -1. But our Lua script checks > 0.
    # So if we validate (INCR -> 1) then release (DECR -> 0).
    if count is None:
        count = 0
    assert int(count) == 0


@pytest.mark.asyncio
async def test_release_safe(rate_limiter):
    """Test that release doesn't go below 0."""
    # Try to release when empty
    await rate_limiter.release()

    count = await rate_limiter.redis.get(rate_limiter.key)
    if count is None:
        count = 0
    assert int(count) == 0


@pytest.mark.asyncio
async def test_concurrent_acquisition(rate_limiter):
    """Test that the Lua script correctly handles concurrent acquisition attempts."""
    # Create 10 concurrent tasks trying to validate slots (capacity is 5)
    tasks = [rate_limiter.validate() for _ in range(10)]

    results = await asyncio.gather(*tasks)

    success_count = results.count(True)
    fail_count = results.count(False)

    assert success_count == 5
    assert fail_count == 5

    actual_count = await rate_limiter.redis.get(rate_limiter.key)
    assert int(actual_count) == 5
