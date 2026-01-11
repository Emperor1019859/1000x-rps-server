import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from loguru import logger

from core.config import settings
from core.kafka import KafkaManager
from core.security import RateLimiter

# Initialize core components
rate_limiter = RateLimiter(redis_url=settings.REDIS_URL, capacity=settings.RATE_LIMIT_CAPACITY)
kafka_manager = KafkaManager(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    tasks_topic=settings.TASKS_TOPIC,
    results_topic=settings.RESULTS_TOPIC,
)
waiting_queue = asyncio.Semaphore(settings.MAX_QUEUE_SIZE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kafka might not be running in the dev environment, so we handle it gracefully
    try:
        await kafka_manager.start()
    except Exception as e:
        logger.warning(f"Failed to connect to Kafka: {e}. Running in degraded mode (mocking results).")
    yield
    await kafka_manager.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.get("/queue")
async def queue():
    # 1. Generate unique request ID
    request_id = str(uuid.uuid4())

    # 2. Concurrency Check (In-flight requests)
    if not await rate_limiter.validate(request_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Server busy, too many in-flight requests. Please try again later.",
        )

    try:
        # 3. Waiting Queue (Local Semaphore for process safety)
        async with waiting_queue:
            # 4. Process via Kafka
            if kafka_manager.producer and kafka_manager.consumer:
                result = await kafka_manager.send_task_and_wait({"action": "root_ping"})
                return {"Hello": "World", "kafka_result": result, "request_id": request_id}
            else:
                # Mock behavior for testing if Kafka is missing
                await asyncio.sleep(0.1)  # Simulate some work
                return {"Hello": "World", "mode": "mocked (no kafka)", "request_id": request_id}
    finally:
        # 5. Always remove from Redis when done (success, failure, or timeout)
        await rate_limiter.release(request_id)


if __name__ == "__main__":
    from uvicorn import run

    run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
