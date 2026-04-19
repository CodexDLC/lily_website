# === STAGE 1: Builder ===
FROM python:3.12-slim AS builder
WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.7

COPY pyproject.toml uv.lock ./
# Бот использует arq и pydantic из codex_tools
RUN uv export --frozen --format requirements.txt --no-hashes --no-dev --no-default-groups --no-emit-project --group bot --group codex_tools --output-file requirements.txt

RUN python -m venv /app/.venv
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# === STAGE 2: Runtime ===
FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /app/.venv /app/.venv

COPY src/telegram_bot /app/src/telegram_bot

RUN chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
CMD ["python", "-m", "src.telegram_bot.app_telegram"]
