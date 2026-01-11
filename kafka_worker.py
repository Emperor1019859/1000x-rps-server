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
    In a real app, this might check a database or call a 3rd party API.
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

    try:
        async for msg in consumer:
            try:
                task_data = json.loads(msg.value.decode())
                correlation_id = task_data.get("correlation_id")

                logger.info(f"Processing task {correlation_id}...")

                # Execute the gift logic
                result_code = await process_task(task_data)

                # Send the result back
                response_payload = {"correlation_id": correlation_id, "result": result_code}
                await producer.send_and_wait(settings.RESULTS_TOPIC, json.dumps(response_payload).encode())
                logger.info(f"Result sent for {correlation_id}")

            except Exception as e:
                logger.error(f"Failed to process message: {e}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # Handle graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(loop.stop()))

    try:
        loop.run_until_complete(run_worker())
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
