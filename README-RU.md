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

Проект использует [uv](https://docs.astral.sh/uv/) для управления зависимостями.

```bash
uv sync
```

`uv sync` поднимает стандартное `dev`-окружение, в которое уже включены обязательные framework-зависимости проекта:

- `codex-django` закреплен как обязательная библиотека Django-слоя для дальнейшего рефакторинга.
- `codex-django-cli` закреплен как обязательный dev/CLI слой для scaffold и управления проектом.

Для production-подобной установки по сервисам используйте явные группы:

```bash
# Backend / Django runtime
uv sync --no-default-groups --group django --group shared --group codex_tools

# Bot / Worker runtime
uv sync --no-default-groups --group bot --group shared --group codex_tools
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
└── pyproject.toml            # Конфигурация uv, Hatchling, Ruff, Mypy
```

---

## 🔧 Инструменты разработки

```bash
# Линтинг и форматирование
uv run ruff check src/
uv run ruff format src/

# Проверка типов
uv run mypy src/

# Тесты
uv run pytest
```

---

© 2026 Lily Beauty Salon. Developed by CodexDLC.
