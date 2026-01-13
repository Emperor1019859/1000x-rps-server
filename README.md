# 1000x RPS FastAPI Server with Kafka Integration

This repository provides a high-performance FastAPI server template optimized for asynchronous task processing using **Kafka** and built-in **Rate Limiting**.

## 🚀 Key Features

- **FastAPI Framework**: Modern, high-performance web framework for Python.
- **Distributed Concurrency Limiting**:
    - Limits **in-flight requests** (default: 100) using Redis.
    - Uses Redis Sets and distributed locks for atomic capacity management.
    - Responds with **429 Too Many Requests** when the capacity is reached.
- **Kafka Integration**:
    - Asynchronous task distribution to Kafka.
    - Request-Response pattern via dedicated `tasks` and `results` topics.
- **Loguru Logging**: Structured and readable logging for easier debugging.
- **High Performance**: Designed to handle bursts and distribute load via worker processes.

## 🏁 Getting Started

### Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/)
- [Apache Kafka](https://kafka.apache.org/) (running on `localhost:9092` by default)
- [Redis](https://redis.io/) (running on `localhost:6379` by default)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/1000x-rps-server.git
    cd 1000x-rps-server
    ```

2.  **Set up environment variables:**
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

3.  **Install dependencies:**
    ```bash
    poetry install
    ```

4.  **Activate virtual environment:**
    ```bash
    poetry shell
    ```

### Docker Mode
If you have Docker installed, you can start everything (FastAPI + Kafka + Redis) with:
```bash
docker-compose up --build
```

## 📊 Benchmarks & Monitoring

### Performance Improvements (v1 vs v2 vs v3)
Recent optimizations have yielded significant improvements in throughput and latency, particularly under heavy load.

| Scenario | Metric | v1 | v2 | v3 | Improvement (v3 vs v1) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **100 Users** | Avg Latency | ~39 ms | ~3 ms | **~3.8 ms** | **90% reduction** |
| | RPS | ~273 | ~304 | **~305** | **12% increase** |
| **1000 Users** | Avg Latency | ~1511 ms | ~99 ms | **~50 ms** | **97% reduction** |
| | RPS | ~492 | ~2318 | **~2700** | **5.5x increase** |

> **Optimization Root Cause:**
> *   **v1 -> v2 (Lua Scripts):** Replaced standard Redis concurrency logic with **Atomic Lua Scripts**, reducing network overhead and locking contention.
> *   **v2 -> v3 (Gunicorn + Workers):** Switched from a single Uvicorn process to **Gunicorn managing 4 Uvicorn workers**. This allows the application to utilize multiple CPU cores effectively, stabilizing latency under high concurrency and further increasing throughput.

### Automated Benchmark Suite
We provide an automated script to simulate 10, 100, and 1000 concurrent users using Locust.
```bash
python benchmarks/run_benchmark.py
```
This script runs three scenarios:
1. **10 Users (Warmup)**: Baseline performance.
2. **100 Users (Load)**: Tests the system at its rated capacity.
3. **1000 Users (Stress)**: Verifies that the rate limiter correctly issues `429 Too Many Requests` beyond the 100-request limit.

Results are saved as CSV files in the `benchmarks/` directory.

### Real-time Dashboard
A complete monitoring stack is included in the Docker Compose setup:
- **Prometheus**: Collects metrics from the web server and cAdvisor.
- **Grafana**: Visualizes metrics (RPS, Latency, Status Codes, CPU/Memory).
    - URL: [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`)
- **cAdvisor**: Monitors container resource usage.

> **Note for macOS Users:** Due to limitations in Docker Desktop for macOS, cAdvisor may not display CPU and Memory usage for specific containers. In such cases, use `docker stats` for local resource monitoring.

## 🧪 Testing

### Unit & Integration Tests
Run standard tests using pytest:
```bash
pytest
```

### End-to-End (E2E) Reliability Tests
The E2E tests simulate real-world scenarios with various user loads (10x, 200x, 1000x users) to verify gift code delivery reliability and uniqueness:
```bash
pytest tests/test_e2e_gift_code.py -s
```

## 📋 TODO
- [x] **Kafka Worker Implementation**: Added `kafka_worker.py` to handle background tasks.
- [x] **Docker Compose**: Add a `docker-compose.yml` to spin up Kafka, Zookeeper, Redis and the FastAPI app together.
- [x] **E2E Reliability Tests**: Added comprehensive E2E tests for high-load scenarios.
- [x] **Real-time Benchmark Dashboard**:
    - [x] **Step 1:** Instrument FastAPI with `prometheus-fastapi-instrumentator`.
    - [x] **Step 2:** Add Prometheus, Grafana, and cAdvisor to `docker-compose.yml`.
    - [x] **Step 3:** Configure Prometheus (`prometheus.yml`) and Grafana datasources/dashboards.
    - [x] **Step 4:** Create `locustfile.py` for 10, 100, 1000 user load simulation.
    - [x] **Step 5:** Build Grafana Dashboard for CPU, Memory, RPS, and Status Codes.
- [x] **Production-Grade Server (Gunicorn)**:
    - [x] Add `gunicorn` dependency.
    - [x] Integrate Gunicorn settings into `core/config.py`.
    - [x] Update `docker-compose.yml` to use Gunicorn with Uvicorn workers.
    - [x] Verify multi-worker performance and stability.
