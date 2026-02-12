# === STAGE 1: Builder ===
FROM python:3.13-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN python -m venv /app/.venv
RUN /app/.venv/bin/pip install --no-cache-dir ".[django]"

# === STAGE 2: Runtime ===
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser
COPY --from=builder /app/.venv /app/.venv
COPY src/backend_django /app/src/backend_django
COPY src/shared /app/src/shared
RUN mkdir -p /app/staticfiles /app/mediafiles /app/data/logs && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/shared:/app/src/backend_django:$PYTHONPATH" # ИЗМЕНЕНО: Добавлено /app/shared в PYTHONPATH
ENV DJANGO_SETTINGS_MODULE="core.settings.dev"
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/ || exit 1
RUN python /app/src/backend_django/manage.py collectstatic --noinput 2>/dev/null || true
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--chdir", "/app/src/backend_django"]
