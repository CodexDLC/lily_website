#!/bin/sh
set -e

# Если передана команда (например, migrate), выполняем только её
if [ "$#" -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
fi

# Иначе запускаем полный цикл запуска приложения
echo "Running collectstatic..."
python /app/manage.py collectstatic --noinput

echo "Running migrations..."
python /app/manage.py migrate --noinput

echo "Loading catalog fixtures..."
python /app/manage.py load_catalog

# Добавляем запуск скрипта обновления контента
echo "Running update_all_content..."
python /app/manage.py update_all_content

# Опциональная миграция из старой базы (Neon)
# Теперь выполняется только если DEBUG=True (локально или в спец. окружении)
if [ "$RUN_LEGACY_MIGRATION" = "true" ] && [ "$DEBUG" = "True" ]; then
    echo "Running migrate_all_legacy from $LEGACY_DATABASE_URL..."
    python /app/manage.py migrate_all_legacy
fi

# Настройка логирования в зависимости от окружения
# Если DEBUG=False (прод), снижаем уровень шума: отключаем access-log и ставим уровень info
if [ "$DEBUG" = "False" ]; then
    GUNICORN_LOG_LEVEL=${LOG_LEVEL:-info}
    GUNICORN_ACCESS_LOG="/dev/null"
    echo "Starting gunicorn in PRODUCTION mode (log_level: $GUNICORN_LOG_LEVEL, access_log: disabled)"
else
    GUNICORN_LOG_LEVEL="debug"
    GUNICORN_ACCESS_LOG="-"
    echo "Starting gunicorn in DEVELOPMENT mode (log_level: $GUNICORN_LOG_LEVEL, access_log: enabled)"
fi

echo "Starting gunicorn..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 90 \
    --access-logfile "$GUNICORN_ACCESS_LOG" \
    --error-logfile - \
    --capture-output \
    --log-level "$GUNICORN_LOG_LEVEL"
