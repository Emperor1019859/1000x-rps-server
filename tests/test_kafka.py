import asyncio
import json
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from core.config import settings
from core.kafka import KafkaManager


@pytest.fixture
async def mock_worker():
    """
    A mock Kafka worker that listens to the tasks topic
    and sends responses to the results topic.
    """
    consumer = AIOKafkaConsumer(
        settings.TASKS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="mock-worker-group",
        auto_offset_reset="latest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()

    stop_event = asyncio.Event()

    async def worker_loop():
        try:
            async for msg in consumer:
                if stop_event.is_set():
                    break

                data = json.loads(msg.value)
                correlation_id = data.get("correlation_id")
                action = data.get("action")

                if action == "get_gift_code":
                    # Simulate processing and sending back a result
                    response = {"correlation_id": correlation_id, "result": f"GIFT-{uuid.uuid4().hex[:8].upper()}"}
                    await producer.send_and_wait(settings.RESULTS_TOPIC, json.dumps(response).encode("utf-8"))
        except Exception as e:
            print(f"Mock worker error: {e}")

    worker_task = asyncio.create_task(worker_loop())

    yield stop_event

    stop_event.set()
    worker_task.cancel()
    await consumer.stop()
    await producer.stop()


@pytest.fixture
async def kafka_manager():
    """Fixture for KafkaManager."""
    manager = KafkaManager(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        tasks_topic=settings.TASKS_TOPIC,
        results_topic=settings.RESULTS_TOPIC,
    )
    await manager.start()
    yield manager
    await manager.stop()


@pytest.mark.asyncio
async def test_kafka_get_gift_code_integration(kafka_manager, mock_worker):
    """
    Test the full round-trip:
    1. KafkaManager sends a 'get_gift_code' task.
    2. Mock worker receives it and sends a response.
    3. KafkaManager receives the response and returns the code.
    """
    # Wait a bit for consumer to settle
    await asyncio.sleep(1)

    gift_code = await kafka_manager.get_gift_code(timeout=10.0)

    assert gift_code is not None
    assert gift_code.startswith("GIFT-")
    assert len(gift_code) > 5


@pytest.mark.asyncio
async def test_kafka_timeout_returns_none(kafka_manager):
    """
    Verify that if no worker responds, it returns None.
    """
    result = await kafka_manager.get_gift_code(timeout=0)
    assert result is None
