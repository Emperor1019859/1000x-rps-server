# Project Context: 1000x-rps-server

## Project Overview
`1000x-rps-server` is a Python-based backend project designed as a high-performance template using the **FastAPI** framework. It aims to handle high throughput (1000+ Requests Per Second) and leverages asynchronous programming. The project uses **Poetry** for dependency management and packaging.

## Key Technologies
*   **Language:** Python (requires >=3.13)
*   **Web Framework:** FastAPI
*   **ASGI Server:** Uvicorn
*   **Dependency Manager:** Poetry
*   **Testing:** pytest, httpx (TestClient)
*   **Linting & Formatting:** Black, isort, Flake8, Pre-commit

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.13+
    *   Poetry

2.  **Install Dependencies:**
    ```bash
    poetry install
    ```

3.  **Activate Virtual Environment:**
    ```bash
    poetry shell
    ```

## Running the Application

*   **Development Mode:**
    You can run the application directly via the `main.py` entry point, which configures `uvicorn` with reload enabled:
    ```bash
    poetry run python main.py
    ```
    Or explicitly with uvicorn:
    ```bash
    poetry run uvicorn main:app --reload
    ```
    The server typically starts at `http://localhost:8000`.

*   **Production Mode:**
    Use `gunicorn` with `uvicorn` workers for concurrency:
    ```bash
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    ```

## Development Workflow & Conventions

*   **Code Style:**
    *   The project strictly adheres to **Black** formatting and **isort** for import sorting.
    *   **Line Length:** 120 characters (configured in `pyproject.toml`).

*   **Linting:**
    *   **Flake8** is used for linting.
    *   **Pre-commit** hooks are configured to enforce these standards automatically (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `black`, `isort`, `flake8`).
    *   Run hooks manually: `poetry run pre-commit run --all-files`

*   **Testing:**
    *   Tests are located in the `tests/` directory.
    *   Run tests using `pytest`:
        ```bash
        poetry run pytest
        ```
    *   The project uses `fastapi.testclient.TestClient` for integration testing of endpoints.

## Directory Structure
*   `main.py`: Application entry point and app definition.
*   `tests/`: Contains test modules (e.g., `test_main.py`).
*   `pyproject.toml`: Poetry configuration, dependency listing, and tool settings (Black, isort).
*   `.pre-commit-config.yaml`: Configuration for Git hooks.
*   `poetry.lock`: Locked dependency versions.
