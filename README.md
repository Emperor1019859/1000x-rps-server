# 1000x RPS FastAPI Server with Kafka Integration

This repository provides a high-performance FastAPI server template optimized for asynchronous task processing using **Kafka** and built-in **Rate Limiting**.

## 🚀 Key Features

- **FastAPI Framework**: Modern, high-performance web framework for Python.
- **Rate Limiting & Queueing**:
    - Enforced **100 Requests Per Second (RPS)** limit.
    - Graceful "waiting" queue for concurrent requests.
    - Responds with **429** when the rate limit is exceeded.
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
If you have Docker installed, you can start everything (FastAPI + Kafka) with:
```bash
docker-compose up --build
```

## ⚡️ Performance & Logic
...
## 📋 TODO
- [ ] **Kafka Worker Implementation**: Create a separate service to consume from the `tasks` topic and produce results to the `results` topic.
- [x] **Docker Compose**: Add a `docker-compose.yml` to spin up Kafka, Zookeeper, and the FastAPI app together.
- [ ] **Monitoring**: Integrate Prometheus/Grafana for real-time RPS and Kafka latency tracking.


## 🤝 Contributing
Contributions are welcome! Please submit a PR for any of the TODO items.

## 📄 License
MIT License
