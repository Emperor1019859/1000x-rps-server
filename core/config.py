from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GIFT_CODE_TIMEOUT: float = 10.0
    TASKS_TOPIC: str = "tasks"
    RESULTS_TOPIC: str = "results"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting Configuration
    RATE_LIMIT_CAPACITY: int = 100
    MAX_QUEUE_SIZE: int = 500
    WORKER_CONCURRENCY: int = 1000

    # Server Configuration (for tests/main)
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    WORKERS: int = 4
    GUNICORN_LOG_LEVEL: str = "info"
    GUNICORN_KEEPALIVE: int = 120

    # Benchmark Configuration
    BENCHMARK_PORT: int = 8001
    NUM_REQUESTS: int = 2000
    CONCURRENCY: int = 100


settings = Settings()
