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

# Добавляем запуск скрипта обновления контента
echo "Running update_all_content..."
python /app/manage.py update_all_content

echo "Starting gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 90
