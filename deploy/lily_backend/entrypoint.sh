#!/bin/sh
set -e

# Если передана команда (например, migrate), выполняем только её
if [ "$#" -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
fi

echo "Starting gunicorn..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 90 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level "${GUNICORN_LOG_LEVEL:-info}"
