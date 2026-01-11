import asyncio
import uuid

import pytest

from core.config import settings
from core.security import RateLimiter


@pytest.fixture
async def rate_limiter():
    """Fixture to provide a RateLimiter instance connected to the test Redis."""
    # Use settings.REDIS_URL which should point to localhost:6379 for local tests
    limiter = RateLimiter(redis_url=settings.REDIS_URL, capacity=5, timeout=2.0)
    # Clear the test key before each test
    await limiter.redis.delete(limiter.key)
    yield limiter
    # Cleanup after test
    await limiter.redis.delete(limiter.key)


@pytest.mark.asyncio
async def test_validate_success(rate_limiter):
    """Test successful acquisition of a slot."""
    request_id = str(uuid.uuid4())
    success = await rate_limiter.validate(request_id)
    assert success is True

    # Verify it exists in Redis
    exists = await rate_limiter.redis.sismember(rate_limiter.key, request_id)
    assert bool(exists) is True

    # Check count
    count = await rate_limiter.redis.scard(rate_limiter.key)
    assert count == 1


@pytest.mark.asyncio
async def test_validate_capacity_exceeded(rate_limiter):
    """Test that acquisition fails when capacity is reached."""
    # Fill up the capacity (capacity is 5 in the fixture)
    for _ in range(5):
        await rate_limiter.validate(str(uuid.uuid4()))

    # Try to validate one more
    extra_id = str(uuid.uuid4())
    success = await rate_limiter.validate(extra_id)
    assert success is False

    # Verify count is still at capacity
    count = await rate_limiter.redis.scard(rate_limiter.key)
    assert count == 5


@pytest.mark.asyncio
async def test_release(rate_limiter):
    """Test releasing a slot."""
    request_id = str(uuid.uuid4())
    await rate_limiter.validate(request_id)

    # Release it
    await rate_limiter.release(request_id)

    # Verify it no longer exists in Redis
    exists = await rate_limiter.redis.sismember(rate_limiter.key, request_id)
    assert bool(exists) is False

    count = await rate_limiter.redis.scard(rate_limiter.key)
    assert count == 0


@pytest.mark.asyncio
async def test_concurrent_acquisition(rate_limiter):
    """Test that the lock correctly handles concurrent acquisition attempts."""
    # Create 10 concurrent tasks trying to validate slots (capacity is 5)
    request_ids = [str(uuid.uuid4()) for _ in range(10)]
    tasks = [rate_limiter.validate(rid) for rid in request_ids]

    results = await asyncio.gather(*tasks)

    success_count = results.count(True)
    fail_count = results.count(False)

    assert success_count == 5
    assert fail_count == 5

    actual_count = await rate_limiter.redis.scard(rate_limiter.key)
    assert actual_count == 5
