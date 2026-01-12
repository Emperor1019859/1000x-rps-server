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
    1. Request enters `POST /queue` endpoint.
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
*   **Reliability Tests (E2E):** `pytest tests/test_e2e_gift_code.py -s`
    *   Verifies 10x, 200x, and 1000x user scenarios.
    *   Ensures >99% success rate and unique gift code delivery.
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

## Roadmap: Real-time Benchmark Dashboard

To achieve a real-time dashboard for monitoring CPU, Memory, RPS, and API status codes under various loads (10, 100, 1000 users), the following plan will be executed:

### Phase 1: Instrumentation
- [x] **FastAPI Metrics:** Add `prometheus-fastapi-instrumentator` to expose `/metrics` endpoint in `main.py`.
- [x] **System Metrics:** Use `cadvisor` or `node_exporter` to expose container CPU/Memory usage.

### Phase 2: Infrastructure (Docker Compose)
- [x] **Prometheus:** Add `prometheus` service to scrape metrics from the web server and system exporters.
- [x] **Grafana:** Add `grafana` service for visualization.
- [x] **cAdvisor:** Add `cadvisor` service to monitor container resource usage.

### Phase 3: Configuration
- [x] **Prometheus Config:** Create `prometheus.yml` to define scrape targets (web-server, cadvisor).
- [x] **Grafana Provisioning:** Configure Grafana to automatically load Prometheus as a datasource and dashboard.

### Phase 4: Load Testing
- [x] **Locust Setup:** Create `locustfile.py` to simulate realistic user behavior.
- [x] **Scenarios:** Define user classes for 10, 100, and 1000 concurrent user tests.

### Phase 5: Visualization
- [x] **Dashboard:** Create a Grafana dashboard JSON model to visualize:
    - **RPS (Throughput):** Rate of requests per second.
    - **Latency:** P50, P95, P99 response times (Available in Grafana).
    - **System Resources:** CPU and Memory usage % (via cAdvisor).
    - **Status Codes:** Breakdown of 2xx, 4xx, 5xx responses.
