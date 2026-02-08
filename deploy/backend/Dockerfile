# Используем официальный легкий образ Python
FROM python:3.13-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry (latest)
RUN pip install poetry

# Копируем файлы зависимостей (контекст сборки - корень проекта)
COPY pyproject.toml poetry.lock ./

# Настраиваем poetry
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости (extras django)
RUN poetry install --no-root --no-interaction --no-ansi --extras django

# Копируем код проекта
COPY src/backend-django /app
COPY src/shared /app/shared

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
