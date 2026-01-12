import asyncio
import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger

from core.config import settings


class KafkaManager:
    """
    Simplified Kafka Manager focused on retrieving gift codes.
    """

    def __init__(self, bootstrap_servers: str, tasks_topic: str, results_topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.tasks_topic = tasks_topic
        self.results_topic = results_topic
        self.producer = None
        self.consumer = None
        self.results = {}  # correlation_id -> asyncio.Future
        self._consume_task = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self.producer.start()

        self.consumer = AIOKafkaConsumer(
            self.results_topic, bootstrap_servers=self.bootstrap_servers, group_id="rps-server-results"
        )
        await self.consumer.start()
        self._consume_task = asyncio.create_task(self._consume_results())
        logger.info("Kafka Producer and Consumer started")

    async def stop(self):
        if self._consume_task:
            self._consume_task.cancel()
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
        logger.info("Kafka Producer and Consumer stopped")

    async def _consume_results(self):
        try:
            async for msg in self.consumer:
                data = json.loads(msg.value)
                correlation_id = data.get("correlation_id")
                if correlation_id in self.results:
                    future = self.results.pop(correlation_id)
                    if not future.done():
                        future.set_result(data.get("result"))
        except Exception as e:
            logger.error(f"Error in Kafka consumer loop: {e}")

    async def get_gift_code(self, timeout: float = settings.KAFKA_GIFT_CODE_TIMEOUT) -> str | None:
        """
        Produces a get_gift_code task and waits for the result.
        Returns the gift code string or None on failure/timeout.
        """
        correlation_id = str(uuid.uuid4())
        payload = {"action": "get_gift_code", "correlation_id": correlation_id}

        future = asyncio.get_running_loop().create_future()
        self.results[correlation_id] = future

        try:
            # Send task
            await self.producer.send_and_wait(self.tasks_topic, json.dumps(payload).encode("utf-8"))
            # Wait for result from consumer loop
            return await asyncio.wait_for(future, timeout=timeout)
        except Exception as e:
            self.results.pop(correlation_id, None)
            logger.warning(f"get_gift_code failed or timed out: {e}")
            return None
