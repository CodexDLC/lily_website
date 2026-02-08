# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder

# Убираем жесткую версию, пусть ставится последняя
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /app

# Install system dependencies for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (latest)
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (only main + bot extras)
RUN poetry install --no-root --no-interaction --no-ansi --extras bot

# === STAGE 2: Runtime ===
FROM python:3.13-slim

WORKDIR /app

# Install runtime libs (libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/telegram_bot /app/src/telegram_bot
COPY src/shared /app/src/shared

RUN chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Start bot (FIXED ENTRYPOINT)
CMD ["python", "-m", "src.telegram_bot.app_telegram"]
