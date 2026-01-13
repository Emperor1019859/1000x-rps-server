from loguru import logger
from redis import asyncio as aioredis


class RateLimiter:
    """
    Redis-backed Concurrency Limiter using a simple counter and Lua scripts for atomicity.
    """

    def __init__(self, redis_url: str, capacity: int):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.capacity = capacity
        self.key = "RATE_LIMIT_COUNTER"

        # Lua script to atomically check and increment
        # Returns 1 if successful (acquired), 0 if capacity exceeded
        self._validate_script = self.redis.register_script(
            """
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local current = tonumber(redis.call('get', key) or "0")
            if current < capacity then
                redis.call('incr', key)
                return 1
            else
                return 0
            end
            """
        )

        # Lua script to safely decrement
        self._release_script = self.redis.register_script(
            """
            local key = KEYS[1]
            local current = tonumber(redis.call('get', key) or "0")
            if current > 0 then
                redis.call('decr', key)
                return 1
            else
                return 0
            end
            """
        )

    async def validate(self) -> bool:
        """
        Check if a new request can be accepted.
        """
        try:
            result = await self._validate_script(keys=[self.key], args=[self.capacity])
            return bool(result)
        except Exception as e:
            logger.error(f"RateLimiter validation error: {e}")
            # Fail closed or open? Standard practice for rate limiting is often fail open (allow),
            # but for concurrency limit to protect system, fail closed (deny) might be safer.
            # Original code returned False on error.
            return False

    async def release(self):
        """
        Decrements the concurrency counter.
        """
        try:
            await self._release_script(keys=[self.key])
        except Exception as e:
            logger.error(f"RateLimiter release error: {e}")
