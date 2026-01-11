import asyncio
import json
import multiprocessing
import time
from datetime import datetime
from pathlib import Path

import httpx
import uvicorn
from loguru import logger

# Configuration
PORT = 8001
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
NUM_REQUESTS = 2000  # Total requests to send
CONCURRENCY = 100  # Number of concurrent tasks
WORKERS = 4  # Number of uvicorn workers
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_FOLDER = PROJECT_ROOT / "benchmarks"


def run_server():
    """Function to run the uvicorn server in a separate process."""
    # vital: disable access log for performance testing to avoid I/O bottlenecks
    # Use "main:app" string to enable workers (required by uvicorn)
    uvicorn.run("main:app", host=HOST, port=PORT, log_level="critical", access_log=False, workers=WORKERS)


async def wait_for_server():
    """Wait for the server to become responsive."""
    async with httpx.AsyncClient() as client:
        for _ in range(50):
            try:
                response = await client.get(BASE_URL)
                if response.status_code == 200:
                    return True
            except httpx.ConnectError:
                await asyncio.sleep(0.1)
    return False


async def fetch(client, semaphore):
    """Perform a single request with concurrency limit."""
    async with semaphore:
        try:
            response = await client.get(BASE_URL)
            return response.status_code
        except Exception:
            return 0


async def benchmark():
    """Run the benchmark."""
    # Use high limits to avoid client-side bottlenecks
    limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)

    # Limit concurrency to avoid opening too many files/sockets at once
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(base_url=BASE_URL, limits=limits) as client:
        start_time = time.time()

        # Create a list of tasks
        tasks = [fetch(client, semaphore) for _ in range(NUM_REQUESTS)]

        # Run them
        results = await asyncio.gather(*tasks)

        end_time = time.time()

        total_time = end_time - start_time
        rps = NUM_REQUESTS / total_time
        success_rate = results.count(200) / NUM_REQUESTS * 100

        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": NUM_REQUESTS,
            "concurrency": CONCURRENCY,
            "workers": WORKERS,
            "total_time_seconds": round(total_time, 4),
            "rps": round(rps, 2),
            "success_rate": round(success_rate, 2),
        }

        logger.info("\n--- Benchmark Results ---")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")

        # Save stats to file
        BENCHMARK_FOLDER.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_path = BENCHMARK_FOLDER / f"benchmark_stats_{now}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)

        return stats


def test_performance():
    """
    Pytest entry point for performance testing.
    This starts the server, runs the benchmark, and asserts a baseline RPS.
    """
    # Start server in a separate process
    # daemon must be False because uvicorn spawns child processes (workers)
    proc = multiprocessing.Process(target=run_server, daemon=False)
    proc.start()

    try:
        # Run the async benchmark
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Wait for server to be up
        is_up = loop.run_until_complete(wait_for_server())
        assert is_up, "Server failed to start"

        # Run benchmark
        stats = loop.run_until_complete(benchmark())
        rps = stats["rps"]

        # Verify it meets a reasonable baseline for a local test
        # Note: 1000 RPS might vary based on the machine running the test
        assert rps > CONCURRENCY, f"RPS {rps} is too low (expected > {CONCURRENCY} for basic health)"

    finally:
        # Cleanup
        proc.terminate()
        proc.join()


if __name__ == "__main__":
    test_performance()
