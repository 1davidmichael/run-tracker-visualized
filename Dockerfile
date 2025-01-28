# Stage 1: Dependency Installation
FROM python:3.13-slim AS builder

# Set working directory inside the container
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv dependency manager
RUN pip install --no-cache-dir uv

# Copy the dependency configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment managed by uv
RUN uv sync --no-dev

# Stage 2: Runtime Environment
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /app /app

# Copy the FastAPI application code
COPY . /app

ENV PATH="/app/.venv/bin:$PATH"

# Expose the application port (default is 8000)
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
