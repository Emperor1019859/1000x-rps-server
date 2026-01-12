import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

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

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.post("/queue")
async def queue() -> dict:
    request_id = str(uuid.uuid4())

    if not await rate_limiter.validate(request_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Server busy, too many in-flight requests. Please try again later.",
        )

    try:
        if kafka_manager.producer and kafka_manager.consumer:
            gift_code = await kafka_manager.get_gift_code(timeout=settings.KAFKA_GIFT_CODE_TIMEOUT)
            return {"gift_code": gift_code, "request_id": request_id}
        return {"gift_code": None, "request_id": request_id}
    finally:
        await rate_limiter.release(request_id)


if __name__ == "__main__":
    from uvicorn import run

    run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
