import asyncio
import json
import signal
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger

from core.config import settings


async def process_task(data):
    """
    THIS IS WHERE THE 'GIFT LOGIC' LIVES.
    """
    action = data.get("action")

    if action == "get_gift_code":
        return f"GIFT-{str(uuid.uuid4()).upper()}"

    return None


async def run_worker():
    logger.info(f"Starting Worker. Connecting to Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")

    consumer = AIOKafkaConsumer(
        settings.TASKS_TOPIC, bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, group_id="gift-service-workers"
    )
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()

    logger.info("Worker is ready and listening for tasks...")

    # Limit concurrency to avoid OOM
    semaphore = asyncio.Semaphore(settings.WORKER_CONCURRENCY)

    async def handle_message(msg):
        async with semaphore:
            try:
                task_data = json.loads(msg.value.decode())
                correlation_id = task_data.get("correlation_id")

                # logger.debug(f"Processing task {correlation_id}...") # Too verbose for high RPS

                result_code = await process_task(task_data)

                response_payload = {"correlation_id": correlation_id, "result": result_code}

                # Non-blocking send
                await producer.send(settings.RESULTS_TOPIC, json.dumps(response_payload).encode())
                # logger.debug(f"Result sent for {correlation_id}")

            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    try:
        async for msg in consumer:
            asyncio.create_task(handle_message(msg))

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Handle graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(loop.stop()))  # This might need better cleanup in loop

    try:
        loop.run_until_complete(run_worker())
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
    finally:
        loop.close()
