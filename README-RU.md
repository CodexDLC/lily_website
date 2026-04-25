# ⚜️ Lily Beauty Salon

[🇬🇧 English](./README.md) | [📖 Документация](https://codexdlc.github.io/lily_website/)

> **Разработка веб-ресурса для салона красоты в Германии.**
>
> 🚀 **Status:** Active Development (Django + HTMX + Email Notifications + ARQ).

---

## 🎯 О проекте

Проект представляет собой профессиональный бизнес-сайт для премиального салона красоты с публичным каталогом услуг и интегрированной системой управления записями (CRM).

### Ключевые этапы
1.  **Публичный сайт (Landing)**:
    *   Презентация топ-мастеров.
    *   Каталог услуг, цены, портфолио работ.
    *   Trust-фактор: Интеграция дипломов и сертификатов.
2.  **Автоматизация**:
    *   Внедрение системы онлайн-записи.
    *   Алгоритм **"Тетрис времени"**: Умный расчет свободных слотов в зависимости от длительности услуг.
3.  **Управление (Личный кабинет)**:
    *   Персонализированный кабинет персонала для управления расписанием.
    *   **Email-уведомления**: Автоматические напоминания клиентам и уведомления о статусах для персонала.
    *   **Magic Login**: Безопасный вход для персонала через email без пароля.

### 🎨 Дизайн-код
*   **Стиль:** Классика, Премиум (Dark Luxury).
*   **Палитра:** 🟢 Глубокий изумрудный, 🟡 Золото, ⚪️ Белый.
*   **Акценты:** Строгая типографика и много "воздуха".

---

## 🛠 Технологический стек

Проект построен на базе модульной features-based архитектуры.

| Компонент | Технология | Описание |
| :--- | :--- | :--- |
| **Backend** | **Django 5.1** | Features-based архитектура, Ninja API |
| **Уведомления** | **Email (SMTP)** | Автоматические рассылки и алерты персоналу |
| **Worker** | **ARQ** | Очередь задач для фоновых процессов |
| **Frontend** | **HTML/CSS/JS** | Django Templates, HTMX, Vanilla JS |
| **Database** | **PostgreSQL** | Основное хранилище данных |
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

### 3. Настройка окружения

Создайте файл `.env` в папке бэкенда:
*   `src/lily_backend/.env`

### 4. Запуск (Local Development)

**Django:**
```bash
cd src/lily_backend
python manage.py migrate
python manage.py runserver
```

**Worker ARQ:**
```bash
# Из корня проекта
uv run arq src.workers.system_worker.worker.WorkerSettings
```

### 5. Настройка PYTHONPATH (Важно!)

Для корректного импорта модулей добавьте корень проекта в PYTHONPATH:

**Linux/macOS:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;$PWD"
```

**PyCharm:**
1. Settings → Project → Project Structure
2. Отметьте корень проекта (`lily_website`) как "Source Root"

**VSCode:**

Создайте `.vscode/settings.json`:
```json
{
    "python.analysis.extraPaths": ["${workspaceFolder}"],
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}"
    },
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder};${env:PYTHONPATH}"
    }
}
```

**Запуск тестов:**
```bash
# Из корня проекта
uv run pytest
```

---

## 📂 Структура проекта

```
lily_website/
├── src/
│   ├── lily_backend/         # Django бэкенд
│   │   ├── system/           # Базовые модели (Client и др.)
│   │   ├── cabinet/          # Интерфейс и сервисы личного кабинета
│   │   ├── core/             # Настройки проекта, URL, логи
│   │   ├── features/         # Модульная бизнес-логика (booking и др.)
│   │   ├── static/           # Глобальная статика
│   │   └── templates/        # Глобальные HTML шаблоны
│   └── workers/              # Фоновые воркеры ARQ
├── deploy/                   # Docker-compose и Nginx конфиги
├── docs/                     # Техническая документация и роадмапы
└── pyproject.toml            # Конфигурация uv, Hatchling, Ruff, Mypy
```

---

## 🔧 Инструменты разработки

```bash
# Линтинг и форматирование
uv run ruff check .
uv run ruff format .

# Проверка типов
uv run mypy src/

# Тесты
uv run pytest
```

---

© 2026 Lily Beauty Salon. Developed by CodexDLC.
