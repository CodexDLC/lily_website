#!/bin/sh
set -e

# Если передана команда (например, migrate), выполняем только её
if [ "$#" -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
fi

# Иначе запускаем полный цикл запуска приложения
echo "Compiling static assets..."
python /app/manage.py compile_assets

echo "Running collectstatic..."
python /app/manage.py collectstatic --noinput

echo "Running migrations..."
python /app/manage.py migrate --noinput

if [ -n "$LEGACY_DATABASE_URL" ]; then
    echo "Importing legacy staff users..."
    python /app/manage.py migrate_users
else
    echo "LEGACY_DATABASE_URL is not set; skipping legacy user import."
fi

echo "Loading catalog fixtures..."
python /app/manage.py load_catalog

# Добавляем запуск скрипта обновления контента
echo "Running update_all_content..."
python /app/manage.py update_all_content

echo "Starting gunicorn..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 90 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level "${GUNICORN_LOG_LEVEL:-info}"
