# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder
WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.7

COPY pyproject.toml uv.lock ./
# Воркеру нужны shared, bot и обязательно codex_tools
RUN uv export --frozen --format requirements.txt --no-hashes --no-dev --no-default-groups --no-emit-project --group bot --group shared --group codex_tools --output-file requirements.txt

RUN python -m venv /app/.venv
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# === STAGE 2: Runtime ===
FROM python:3.13-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /app/.venv /app/.venv

COPY src/workers /app/src/workers
COPY src/shared /app/src/shared

# Создаем папку для логов и устанавливаем права
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
