# ⚜️ Lily Beauty Salon

[🇬🇧 English](./README.md) | [📖 Документация](https://codexdlc.github.io/lily_website/)

> **Разработка веб-ресурса для салона красоты в Германии.**
>
> 🚀 **Status:** Active Development (Django + Telegram Bot + ARQ Worker).

---

## 🎯 О проекте

Проект представляет собой имиджевую витрину салона красоты с последующей трансформацией в полноценную систему управления записями (CRM).

### Ключевые этапы
1.  **Витрина (MVP)**:
    *   Презентация топ-мастеров (Liliia Yakina).
    *   Каталог услуг, цены, портфолио работ.
    *   Trust-фактор: Интеграция дипломов и сертификатов.
2.  **Автоматизация**:
    *   Внедрение системы онлайн-записи.
    *   Алгоритм **"Тетрис времени"**: Умный расчет свободных слотов в зависимости от длительности услуг.
3.  **Управление (Telegram Bot)**:
    *   Мгновенные уведомления персонала о новых записях.
    *   Управление расписанием через мессенджер.

### 🎨 Дизайн-код
*   **Стиль:** Классика, Премиум (Dark Luxury).
*   **Палитра:** 🟢 Глубокий изумрудный, 🟡 Золото, ⚪️ Белый.
*   **Акценты:** Строгая типографика и много "воздуха".

---

## 🛠 Технологический стек

Проект построен на базе модульного монорепозитория (Django + Aiogram + ARQ).

| Компонент | Технология | Описание |
| :--- | :--- | :--- |
| **Backend** | **Django 5.1** | Features-based архитектура, Ninja API |
| **Bot** | **Aiogram 3.x** | Асинхронный бот, интеграция с Redis Stream |
| **Worker** | **ARQ** | Очередь задач для уведомлений |
| **Frontend** | **HTML/CSS/JS** | Django Templates, HTMX, Vanilla JS |
| **Database** | **PostgreSQL** | Изоляция схем (`django_app`, `bot_app`) |
| **Cache** | **Redis** | Кэширование, сессии, очередь задач |
| **Infra** | **Docker** | Docker Compose, Nginx, GitHub Actions |

---

## 🚀 Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/codexdlc/lily_website.git
cd lily_website
```

### 2. Установка зависимостей

Используется [Poetry](https://python-poetry.org/) для управления зависимостями.

```bash
pip install poetry
poetry config virtualenvs.in-project true
poetry install --extras "django bot dev"
```

### 3. Настройка окружения

Создайте файлы `.env` в папках компонентов:
*   `src/backend_django/.env`
*   `src/telegram_bot/.env`

### 4. Запуск (Local Development)

**Django:**
```bash
cd src/backend_django
python manage.py migrate
python manage.py runserver
```

**Telegram Bot:**
```bash
python -m src.telegram_bot.app_telegram
```

**Worker ARQ:**
```bash
arq src.workers.notification_worker.worker.WorkerSettings
```

---

## 📂 Структура проекта

```
lily_website/
├── src/
│   ├── backend_django/       # Django бэкенд (features-based структура)
│   │   ├── api/              # Ninja API эндпоинты
│   │   ├── core/             # Настройки, urls, конфиг логирования
│   │   ├── features/         # Бизнес-логика (booking, cabinet и др.)
│   │   ├── static/           # Статика (CSS, JS, IMG)
│   │   └── templates/        # HTML шаблоны
│   ├── telegram_bot/         # Telegram Bot (aiogram 3.x)
│   ├── workers/              # Фоновые воркеры ARQ
│   └── shared/               # Общий код (схемы, утилиты, ядро)
├── deploy/                   # Docker-compose и Nginx конфиги
├── docs/                     # Техническая документация и роадмапы
└── pyproject.toml            # Конфигурация Poetry, Ruff, Mypy
```

---

## 🔧 Инструменты разработки

```bash
# Линтинг и форматирование
ruff check src/
ruff format src/

# Проверка типов
mypy src/

# Тесты
pytest
```

---

© 2026 Lily Beauty Salon. Developed by CodexDLC.
