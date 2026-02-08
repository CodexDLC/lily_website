# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder

WORKDIR /app

RUN python -m venv /app/.venv

# Install dependencies via pyproject.toml
COPY pyproject.toml ./
RUN /app/.venv/bin/pip install --no-cache-dir ".[bot]"

# === STAGE 2: Runtime ===
FROM python:3.13-slim

WORKDIR /app

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

# Start bot
CMD ["python", "-m", "src.telegram_bot.app_telegram"]
