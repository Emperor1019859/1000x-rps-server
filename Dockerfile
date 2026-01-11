FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.2.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create a virtual environment inside the container
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

# Install the project itself
RUN poetry install --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
