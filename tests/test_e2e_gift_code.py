import asyncio
import json
import os
import shutil
import subprocess
import uuid

import httpx
import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger

from core.config import settings
from core.security import RateLimiter

# Constants for E2E test
PORT = 8003
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"


async def run_mock_worker(group_id):
    """Run a mock Kafka worker with a specific group ID."""
    consumer = AIOKafkaConsumer(
        settings.TASKS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset="earliest",  # Better for tests to avoid missing messages
    )
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()

    logger.info(f"Worker {group_id} started")
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            correlation_id = data.get("correlation_id")
            action = data.get("action")

            if action == "get_gift_code":
                # Simulate fast processing
                await asyncio.sleep(0.01)
                response = {"correlation_id": correlation_id, "result": f"GIFT-{uuid.uuid4().hex[:6].upper()}"}
                await producer.send_and_wait(settings.RESULTS_TOPIC, json.dumps(response).encode())
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await consumer.stop()
        await producer.stop()


def start_worker_process(group_id):
    # We still use multiprocessing for the worker to keep it independent of the async loop of the test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_mock_worker(group_id))
    except Exception as e:
        logger.error(f"Worker process error: {e}")


async def wait_for_server():
    async with httpx.AsyncClient() as client:
        for _ in range(100):  # Increased retries for gunicorn startup
            try:
                response = await client.get(BASE_URL)
                if response.status_code == 200:
                    return True
            except httpx.ConnectError:
                await asyncio.sleep(0.1)
    return False


async def send_requests(num_requests, concurrency):
    semaphore = asyncio.Semaphore(concurrency)

    async def task(client):
        async with semaphore:
            try:
                resp = await client.post("/queue", timeout=15.0)
                # Return a dict with the results we need
                return {"status_code": resp.status_code, "json": resp.json() if resp.status_code == 200 else None}
            except Exception as e:
                return {"status_code": 0, "error": str(e)}

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
    async with httpx.AsyncClient(base_url=BASE_URL, limits=limits) as client:
        tasks = [task(client) for _ in range(num_requests)]
        return await asyncio.gather(*tasks)


async def run_scenario(num_users, concurrency):
    """Generic runner for a single scenario."""
    # Clean Redis
    rl = RateLimiter(settings.REDIS_URL, settings.RATE_LIMIT_CAPACITY)
    await rl.redis.delete(rl.key)
    await rl.redis.aclose()

    # Unique group for this specific test run
    worker_group = f"e2e-worker-{uuid.uuid4().hex[:6]}"

    # Start Server with subprocess.Popen
    cmd = [
        "gunicorn",
        "main:app",
        "--workers",
        "4",
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "--bind",
        f"{HOST}:{PORT}",
        "--log-level",
        "error",
    ]

    # Ensure PROMETHEUS_MULTIPROC_DIR is set and exists
    env = os.environ.copy()
    multiproc_dir = f"/tmp/prometheus_multiproc_test_{uuid.uuid4().hex}"
    os.makedirs(multiproc_dir, exist_ok=True)
    env["PROMETHEUS_MULTIPROC_DIR"] = multiproc_dir

    # Use start_new_session to ensure we can kill the whole process group if needed
    server_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    # Start Worker
    import multiprocessing

    worker_proc = multiprocessing.Process(target=start_worker_process, args=(worker_group,))
    worker_proc.start()

    try:
        if not await wait_for_server():
            logger.error("Server failed to start within timeout.")
            # Print stderr/stdout if possible? (redirected to DEVNULL above)
            raise RuntimeError("Server failed to start")

        # Wait for Kafka consumers to settle
        await asyncio.sleep(5)

        logger.info(f"Starting Scenario: {num_users} users, {concurrency} concurrency")
        results = await send_requests(num_users, concurrency)

        status_counts = {}
        gift_codes = []
        for r in results:
            sc = r["status_code"]
            status_counts[sc] = status_counts.get(sc, 0) + 1
            if sc == 200 and r["json"] and r["json"].get("gift_code"):
                gift_codes.append(r["json"]["gift_code"])

        success_rate = (status_counts.get(200, 0) / num_users) * 100
        logger.info(f"Results: {status_counts}, Success Rate: {success_rate:.1f}%, Codes: {len(gift_codes)}")

        return status_counts, gift_codes
    finally:
        # Terminate Server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

        # Terminate Worker
        worker_proc.terminate()
        worker_proc.join()

        # Cleanup multiproc dir
        if os.path.exists(multiproc_dir):
            shutil.rmtree(multiproc_dir)


@pytest.mark.asyncio
async def test_e2e_10_users():
    status_counts, gift_codes = await run_scenario(10, 10)
    assert status_counts.get(200) == 10
    assert len(gift_codes) == 10
    assert len(set(gift_codes)) == 10


@pytest.mark.asyncio
async def test_e2e_200_users():
    status_counts, gift_codes = await run_scenario(200, 50)
    # Success rate should be very high
    assert status_counts.get(200, 0) >= 198
    assert len(gift_codes) == status_counts.get(200)
    assert len(set(gift_codes)) == len(gift_codes)


@pytest.mark.asyncio
async def test_e2e_1000_users():
    status_counts, gift_codes = await run_scenario(1000, 100)
    # Success rate should be >= 99%
    success_count = status_counts.get(200, 0)
    assert (success_count / 1000) >= 0.99
    assert len(gift_codes) == success_count
    assert len(set(gift_codes)) == len(gift_codes)
