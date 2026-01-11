from loguru import logger
from redis import asyncio as aioredis


class RateLimiter:
    """
    Redis-backed Concurrency Limiter using a Set for O(1) operations.
    Protected by a distributed lock to ensure atomic capacity checks.
    """

    def __init__(self, redis_url: str, capacity: int, timeout: float = 5.0):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.capacity = capacity
        self.timeout = timeout
        self.key = "RATE_LIMIT_CAPACITY_SET"
        self.lock_name = "RATE_LIMIT_LOCK"

    async def validate(self, request_id: str) -> bool:
        """
        Check if a new request can be accepted.
        """
        lock = self.redis.lock(self.lock_name, timeout=self.timeout, blocking_timeout=self.timeout)
        try:
            if await lock.acquire():
                try:
                    current_count = await self.redis.scard(self.key)
                    if current_count < self.capacity:
                        await self.redis.sadd(self.key, request_id)
                        return True
                    return False
                finally:
                    await lock.release()
            else:
                logger.debug(f"Lock {self.lock_name} acquisition timed out for {request_id}")
                return False
        except Exception as e:
            logger.error(f"RateLimiter acquisition error: {e}")
            return False

    async def release(self, request_id: str):
        """
        Removes the request_id from the set in O(1) time.
        """
        try:
            await self.redis.srem(self.key, request_id)
        except Exception as e:
            logger.error(f"RateLimiter release error for {request_id}: {e}")
