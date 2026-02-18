# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install poetry poetry-plugin-export

COPY pyproject.toml poetry.lock ./
RUN poetry lock
# Экспортируем основные зависимости + django + shared (arq и др.)
RUN poetry export --without-hashes --with django,shared --format=requirements.txt > requirements.txt

RUN python -m venv /venv
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# === STAGE 2: Runtime ===
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 appuser

COPY --from=builder /venv /venv
COPY src/backend_django /app
COPY deploy/backend/entrypoint.sh /entrypoint.sh

# Оптимизируем слои: создаем папки, меняем владельца и права за один RUN
RUN mkdir -p /app/staticfiles /app/media /app/logs/backend && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/media /app/logs/backend && \
    chmod +x /entrypoint.sh

USER appuser

ENV PATH="/venv/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE="core.settings.dev"

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/api/v1/health || exit 1

WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
