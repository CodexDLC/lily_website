# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder
WORKDIR /app
RUN python -m venv /app/.venv
COPY pyproject.toml ./
RUN /app/.venv/bin/pip install --no-cache-dir ".[bot]"

# === STAGE 2: Runtime ===
FROM python:3.13-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /app/.venv /app/.venv
COPY src/telegram_bot /app/src/telegram_bot
COPY src/worker_arq /app/src/worker_arq
COPY src/shared /app/src/shared
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
CMD ["python", "-m", "src.worker_arq.bot_worker"]
