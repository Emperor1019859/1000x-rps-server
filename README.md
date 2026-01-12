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

### Performance Benchmarks
Run high-concurrency benchmarks:
```bash
pytest tests/test_performance_100x.py -s
```

## ⚡️ Performance & Logic
...
## 📋 TODO
- [x] **Kafka Worker Implementation**: Added `kafka_worker.py` to handle background tasks.
- [x] **Docker Compose**: Add a `docker-compose.yml` to spin up Kafka, Zookeeper, Redis and the FastAPI app together.
- [x] **E2E Reliability Tests**: Added comprehensive E2E tests for high-load scenarios.
- [ ] **Real-time Benchmark Dashboard**:
    - [ ] **Step 1:** Instrument FastAPI with `prometheus-fastapi-instrumentator`.
    - [ ] **Step 2:** Add Prometheus, Grafana, and cAdvisor to `docker-compose.yml`.
    - [ ] **Step 3:** Configure Prometheus (`prometheus.yml`) and Grafana datasources.
    - [ ] **Step 4:** Create `locustfile.py` for 10, 100, 1000 user load simulation.
    - [ ] **Step 5:** Build Grafana Dashboard for CPU, Memory, RPS, and Status Codes.


## 🤝 Contributing
Contributions are welcome! Please submit a PR for any of the TODO items.

## 📄 License
MIT License
