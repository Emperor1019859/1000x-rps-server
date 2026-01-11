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
    1. Every request is assigned a `uuid4`.
    2. The ID is added to a Redis set (`RATE_LIMIT_CAPACITY_SET`) if the set size is below capacity.
    3. Atomicity is ensured using a Redis-backed distributed lock.
    4. If capacity is exceeded, the server returns `429 Too Many Requests`.
    5. Upon completion (Kafka response, timeout, or error), the ID is removed from Redis via a `finally` block in the endpoint.
*   **Kafka Flow:**
    1. Request enters `queue` endpoint.
    2. Produced to `tasks` topic with a `correlation_id`.
    3. Server subscribes to `results` topic.
    4. Result is matched via `correlation_id` and returned to user.

## Setup and Installation
1.  **Install Dependencies:** `poetry install`
2.  **Environment:** Ensure a Kafka broker is running at `localhost:9092`.

## Running the Application
*   **Development:** `poetry run python main.py`
*   **Production:** `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000`

## Development Workflow
*   **Formatters:** Black (120 line length), isort.
*   **Linting:** Flake8.
*   **Performance Tests:** `pytest tests/test_performance_100x.py -s`
    *   Saves statistics to `benchmark_stats.json`.

## Directory Structure
*   `main.py`: Application entry point and app definition.
*   `.env.example`: Template for environment variables.
*   `Dockerfile`: Container definition.
*   `docker-compose.yml`: Orchestration for web-server, Kafka, and Redis.
*   `core/`: Core application logic.
    *   `config.py`: Settings & .env loading.
    *   `security.py`: Rate limiting logic.
    *   `kafka.py`: Kafka producer/consumer management.
*   `tests/`: Contains test modules (e.g., `test_main.py`, `test_performance_100x.py`).
*   `pyproject.toml`: Poetry configuration, dependency listing, and tool settings (Black, isort).
