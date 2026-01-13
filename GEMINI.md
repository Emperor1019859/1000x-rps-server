# Project Context: 1000x-rps-server

## Project Overview
`1000x-rps-server` is a high-performance FastAPI template. It features a robust architecture that combines **Rate Limiting** (100 RPS) with **Kafka-based asynchronous processing** to handle high-throughput workloads while preventing system overload.

## Key Technologies
*   **Language:** Python (>=3.13, <4.0)
*   **Web Framework:** FastAPI
*   **Messaging:** Kafka (via `aiokafka`)
*   **Rate Limiting:** Redis-backed Concurrency Limiter using a Set and distributed Lock in `core/security.py`.
*   **Configuration:** `pydantic-settings` for environment-based configuration in `core/config.py`.
*   **Logging:** `loguru`
*   **Storage:** Redis (for distributed concurrency limiting)
*   **Dependency Manager:** Poetry
*   **Testing:** `pytest`, `httpx` (includes performance benchmarks)

## Architecture Details
*   **Settings Management:** All constants are centralized in `core/config.py` and can be overridden via `.env` file or environment variables.
*   **Distributed Concurrency Limiting:** Limits **active in-flight requests** to 100 using Redis.
    1.  Uses an **Atomic Lua Script** for high-performance concurrency management.
    2.  Atomicity is guaranteed on the Redis server side, eliminating network RTT for locking.
    3.  If capacity is exceeded, the server returns `429 Too Many Requests`.
    4.  Upon completion, the counter is decremented via another Lua script in a `finally` block.
*   **Kafka Flow:**
    1.  Request enters `POST /queue` endpoint.
    2.  Produced to `tasks` topic with a `correlation_id`.
    3.  Server subscribes to `results` topic using a **unique group_id per instance** (to support multi-worker/multi-node deployments).
    4.  Result is matched via `correlation_id` and returned to user.

## Setup and Installation
1.  **Install Dependencies:** `poetry install`
2.  **Environment:** Ensure a Kafka broker is running at `localhost:9092` and Redis at `localhost:6379`.

## Running the Application
*   **Development:** `poetry run python main.py`
*   **Production:** `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --keep-alive 120`

## Development Workflow
*   **Formatters:** Black (120 line length), isort.
*   **Linting:** Flake8.
*   **Reliability Tests (E2E):** `pytest tests/test_e2e_gift_code.py -v -s`
    *   Verifies 10x, 200x, and 1000x user scenarios.
    *   Ensures >99% success rate and unique gift code delivery.
*   **Benchmarks:** `python benchmarks/run_benchmark.py`
    *   Simulates realistic load using Locust and saves statistics.

## Monitoring & Benchmarking
The project includes a full-featured monitoring stack and automated benchmark suite.

*   **Prometheus & Grafana:** Pre-configured with a "RPS Performance Dashboard".
*   **cAdvisor:** Container resource monitoring.
*   **Locust:** Load testing tool.
*   **Automated Suite:** `benchmarks/run_benchmark.py` for standard 10/100/1000 user scenarios.

## Directory Structure
*   `main.py`: Application entry point and app definition.
*   `.env.example`: Template for environment variables.
*   `Dockerfile`: Container definition.
*   `docker-compose.yml`: Orchestration for web-server, Kafka, Redis, and Monitoring.
*   `benchmarks/`: Automated benchmark scripts and CSV results.
*   `monitoring/`: Configuration for Prometheus and Grafana.
*   `core/`: Core application logic.
    *   `config.py`: Settings & .env loading.
    *   `security.py`: Rate limiting logic.
    *   `kafka.py`: Kafka producer/consumer management.
*   `tests/`: Contains test modules (e.g., `test_main.py`, `test_e2e_gift_code.py`).
*   `pyproject.toml`: Poetry configuration, dependency listing, and tool settings (Black, isort).
