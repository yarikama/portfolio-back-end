# Base Stage:
FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH="/app"

WORKDIR /app

COPY pyproject.toml uv.lock ./

# Development Stage: include dev dependencies + hot reload
FROM base AS dev

# Install all dependencies to system Python (without creating .venv)
# This way volume mount won't overwrite installed packages
RUN uv pip install --no-cache -e ".[dev]"

COPY . .

# Development use: uvicorn with --reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# Production Stage: minimal, only necessary things
FROM base AS production

ENV UV_COMPILE_BYTECODE=1

# Install only production dependencies to system Python
RUN uv pip install --no-cache .

COPY ./app ./
COPY ./ml/model ./ml/model

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
