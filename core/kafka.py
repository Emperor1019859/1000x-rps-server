import asyncio
import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import HTTPException, status
from loguru import logger


class KafkaManager:
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

    async def send_task_and_wait(self, payload: dict, timeout: float = 5.0):
        correlation_id = str(uuid.uuid4())
        payload["correlation_id"] = correlation_id

        future = asyncio.get_running_loop().create_future()
        self.results[correlation_id] = future

        try:
            await self.producer.send_and_wait(self.tasks_topic, json.dumps(payload).encode("utf-8"))
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.results.pop(correlation_id, None)
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Task processing timed out")
        except Exception as e:
            self.results.pop(correlation_id, None)
            logger.error(f"Kafka error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred"
            )
