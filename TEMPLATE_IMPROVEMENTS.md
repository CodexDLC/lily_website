# Template Improvements Report

**Проект:** lily_website
**Дата:** 2026-02-12
**Автор:** Claude Sonnet 4.5
**План:** [expressive-noodling-flamingo.md](C:\Users\prime\.claude\plans\expressive-noodling-flamingo.md)

---

## Цель документа

Этот отчет документирует проблемы, найденные в проекте lily_website, который был создан из шаблона (template). Цель — предоставить конкретные исправления для применения в главном template, чтобы избежать этих проблем в будущих проектах.

---

## Краткое резюме проблем

| # | Проблема | Файл | Критичность |
|---|----------|------|-------------|
| 1 | Неправильный PYTHONPATH в Backend Dockerfile | `deploy/backend/Dockerfile` | 🔴 Высокая |
| 2 | Несогласованность volumes в docker-compose.yml | `deploy/docker-compose.yml` | 🔴 Высокая |
| 3 | Отсутствие явного PYTHONPATH в Bot/Worker Dockerfiles | `deploy/bot/Dockerfile`, `deploy/worker/Dockerfile` | 🟡 Средняя |
| 4 | Неправильные пути к manage.py в CI/CD | `.github/workflows/cd-release.yml` | 🟡 Средняя |
| 5 | Отсутствие pythonpath в pytest конфиге | `pyproject.toml` | 🟢 Низкая |
| 6 | Отсутствие документации по PYTHONPATH | `README.md` | 🟢 Низкая |

---

## Детальное описание проблем

### Проблема #1: Неправильный PYTHONPATH в Backend Dockerfile

**Файл:** `deploy/backend/Dockerfile`
**Строки:** 20, 23

**Суть проблемы:**

В Dockerfile файлы копируются в `/app/src/shared` и `/app/src/backend_django` (строки 15-16), но PYTHONPATH указывает на `/app/shared` вместо `/app`:

```dockerfile
# Строка 15-16: Копируем файлы
COPY src/backend_django /app/src/backend_django
COPY src/shared /app/src/shared

# Строка 20: Неправильный PYTHONPATH
ENV PYTHONPATH="/app/shared:/app/src/backend_django:$PYTHONPATH"
```

**Почему это проблема:**
- Импорты вида `from src.shared.xxx import yyy` не работают
- PYTHONPATH `/app/shared` ищет модули в `/app/shared/core/...`, но файлы в `/app/src/shared/core/...`
- Противоречие между COPY и PYTHONPATH

**Дополнительная проблема (строка 23):**
```dockerfile
RUN python /app/src/backend_django/manage.py collectstatic --noinput 2>/dev/null || true
```
Использует абсолютный путь вместо относительного с `cd`.

---

### Проблема #2: Несогласованность volumes в docker-compose.yml

**Файл:** `deploy/docker-compose.yml`
**Строки:** 7, 13-14

**Суть проблемы:**

Backend и Bot/Worker монтируют shared по-разному:

```yaml
# Backend (неправильно):
volumes:
  - ../src/backend_django:/app              # Монтирует в /app
  - ../src/shared:/app/shared               # Монтирует в /app/shared ❌

# Bot (правильно):
volumes:
  - ../src/telegram_bot:/app/src/telegram_bot:ro
  - ../src/shared:/app/src/shared:ro        # Монтирует в /app/src/shared ✅
```

**Почему это проблема:**
- Несогласованность между сервисами
- Backend монтирует в `/app/shared`, но ожидает `/app/src/shared` (из-за импортов `from src.shared`)
- Разработка в Docker работает иначе чем production build (где файлы копируются правильно)

**Дополнительная проблема (строка 7):**
```yaml
command: python manage.py runserver 0.0.0.0:8000
```
Использует относительный путь к `manage.py`, но workdir теперь должен быть `/app`, а не `/app/src/backend_django`.

---

### Проблема #3: Отсутствие явного PYTHONPATH в Bot/Worker

**Файлы:**
- `deploy/bot/Dockerfile` (после строки 17)
- `deploy/worker/Dockerfile` (после строки 16)

**Суть проблемы:**

Bot и Worker Dockerfiles не имеют явной декларации `ENV PYTHONPATH`, полагаясь на то что `python -m src.xxx` автоматически добавит пути.

**Почему это проблема:**
- Неявное поведение — сложнее отлаживать
- Отсутствие единообразия между всеми сервисами
- Потенциальные проблемы если кто-то изменит команду запуска

---

### Проблема #4: Неправильные пути в CI/CD

**Файл:** `.github/workflows/cd-release.yml`
**Строки:** 42, 75-76

**Суть проблемы:**

1. **Строка 42:** Указан неправильный путь к Worker Dockerfile:
```yaml
file: deploy/worker_arq/Dockerfile  # ❌ Должно быть deploy/worker/Dockerfile
```

2. **Строки 75-76:** Пути к `manage.py` без учета новой структуры:
```yaml
docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py migrate --noinput
# ❌ Должно быть: python src/backend_django/manage.py migrate --noinput
```

**Почему это проблема:**
- CI/CD упадет при деплое
- Миграции и collectstatic не выполнятся

---

### Проблема #5: Отсутствие pythonpath в pytest

**Файл:** `pyproject.toml`
**Строка:** После 91

**Суть проблемы:**

Pytest конфигурация не содержит `pythonpath = ["."]`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["src"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
# pythonpath = ["."]  ← Отсутствует!
```

**Почему это проблема:**
- Тесты не находят модуль `src.shared` при локальном запуске
- Разработчики должны вручную устанавливать PYTHONPATH
- Неконсистентное поведение между разными окружениями

---

### Проблема #6: Отсутствие документации PYTHONPATH

**Файл:** `README.md`

**Суть проблемы:**

В README.md нет информации о том, что для локальной разработки нужно настроить PYTHONPATH. Секция "Run (Local Development)" содержит команды, но не предупреждает о необходимости настройки окружения.

**Почему это проблема:**
- Новые разработчики столкнутся с `ModuleNotFoundError: No module named 'src'`
- Неясно как настроить IDE (PyCharm, VSCode)
- Нет инструкций для разных ОС (Windows, Linux, macOS)

---

## Рекомендуемые исправления для template

### Исправление #1: Backend Dockerfile

**Файл:** `deploy/backend/Dockerfile`

```diff
  COPY src/backend_django /app/src/backend_django
  COPY src/shared /app/src/shared
  RUN mkdir -p /app/staticfiles /app/mediafiles /app/data/logs && chown -R appuser:appuser /app
  USER appuser
  ENV PATH="/app/.venv/bin:$PATH"
- ENV PYTHONPATH="/app/shared:/app/src/backend_django:$PYTHONPATH"
+ ENV PYTHONPATH="/app:$PYTHONPATH"
  ENV DJANGO_SETTINGS_MODULE="core.settings.dev"
  HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/ || exit 1
- RUN python /app/src/backend_django/manage.py collectstatic --noinput 2>/dev/null || true
+ RUN cd /app/src/backend_django && python manage.py collectstatic --noinput 2>/dev/null || true
  CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--chdir", "/app/src/backend_django"]
```

**Обоснование:**
- `/app` содержит всю структуру `src/` (backend_django, telegram_bot, shared)
- Упрощает PYTHONPATH до одного корневого пути
- `cd /app/src/backend_django &&` гарантирует правильный рабочий каталог для collectstatic

---

### Исправление #2: docker-compose.yml

**Файл:** `deploy/docker-compose.yml`

```diff
  backend:
    build:
      context: ..
      dockerfile: deploy/backend/Dockerfile
    container_name: lily_website-backend
-   command: python manage.py runserver 0.0.0.0:8000
+   command: python src/backend_django/manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file:
      - ../src/backend_django/.env
    volumes:
-     - ../src/backend_django:/app
-     - ../src/shared:/app/shared
+     - ../src/backend_django:/app/src/backend_django
+     - ../src/shared:/app/src/shared:ro
      - uploads:/app/media
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - lily_website-network
```

**Обоснование:**
- Приводит к единообразию с bot и worker сервисами
- Монтирует shared в правильное место `/app/src/shared`
- `:ro` (read-only) предотвращает случайное изменение shared из backend
- Команда запуска указывает полный путь к manage.py с учетом нового workdir

---

### Исправление #3: Bot Dockerfile

**Файл:** `deploy/bot/Dockerfile`

```diff
  COPY --from=builder /app/.venv /app/.venv
  COPY src/telegram_bot /app/src/telegram_bot
  COPY src/shared /app/src/shared
  RUN chown -R appuser:appuser /app
  USER appuser
  ENV PATH="/app/.venv/bin:$PATH"
+ ENV PYTHONPATH="/app:$PYTHONPATH"
  CMD ["python", "-m", "src.telegram_bot.app_telegram"]
```

**Обоснование:**
- Явная декларация PYTHONPATH для последовательности
- Гарантирует что импорты работают одинаково во всех контейнерах
- Упрощает отладку

---

### Исправление #4: Worker Dockerfile

**Файл:** `deploy/worker/Dockerfile`

**⚠️ ВНИМАНИЕ:** В lily_website Worker был перемещен в `src/worker_arq/`. В базовом template Worker находится в `src/telegram_bot/services/worker/`. Адаптируйте изменения под свою структуру.

**Для базового template:**
```diff
  COPY --from=builder /app/.venv /app/.venv
  COPY src/telegram_bot /app/src/telegram_bot
  COPY src/shared /app/src/shared
  USER appuser
  ENV PATH="/app/.venv/bin:$PATH"
+ ENV PYTHONPATH="/app:$PYTHONPATH"
  CMD ["python", "-m", "src.telegram_bot.services.worker.bot_worker"]
```

**Для lily_website (с отдельным worker_arq):**
```diff
  COPY --from=builder /app/.venv /app/.venv
  COPY src/telegram_bot /app/src/telegram_bot
+ COPY src/worker_arq /app/src/worker_arq
  COPY src/shared /app/src/shared
  USER appuser
  ENV PATH="/app/.venv/bin:$PATH"
+ ENV PYTHONPATH="/app:$PYTHONPATH"
- CMD ["python", "-m", "src.telegram_bot.services.worker.bot_worker"]
+ CMD ["python", "-m", "src.worker_arq.bot_worker"]
```

---

### Исправление #5: CI/CD workflows

**Файл:** `.github/workflows/cd-release.yml`

```diff
  - name: Build and Push Worker
    uses: docker/build-push-action@v5
    with:
      context: .
-     file: deploy/worker_arq/Dockerfile
+     file: deploy/worker/Dockerfile
      push: true
      tags: ghcr.io/${{ env.REPO_LOWER }}-worker_arq:latest
```

```diff
  docker compose -f deploy/docker-compose.prod.yml pull
- docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py migrate --noinput
- docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py collectstatic --noinput
+ docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python src/backend_django/manage.py migrate --noinput
+ docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python src/backend_django/manage.py collectstatic --noinput
  docker compose -f deploy/docker-compose.prod.yml up -d --remove-orphans --wait
```

**Обоснование:**
- Правильный путь к Worker Dockerfile
- Пути к manage.py учитывают что workdir это `/app`, а не `/app/src/backend_django`

---

### Исправление #6: pytest конфигурация

**Файл:** `pyproject.toml`

```diff
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["src"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
+ pythonpath = ["."]
```

**Обоснование:**
- Pytest автоматически добавит корень проекта в PYTHONPATH
- Тесты будут работать "из коробки" без дополнительной настройки

---

### Исправление #7: Документация README.md

**Файл:** `README.md`

**Добавить новую секцию после "Run (Local Development)":**

```markdown
### 5. Python Path Configuration (Important!)

For correct module imports, add the project root to PYTHONPATH:

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
2. Mark the project root as "Source Root"

**VSCode:**

Create `.vscode/settings.json`:
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

**Running Tests:**
```bash
# From project root
pytest src/
```
```

**Также обновить команды запуска:**

```diff
  **Django:**
  ```bash
  cd src/backend_django
  python manage.py migrate
  python manage.py runserver
  ```

  **Telegram Bot:**
  ```bash
- cd src/telegram_bot
- # Ensure DB is running and migrations are applied
- alembic upgrade head
- python -m core
+ python -m src.telegram_bot.app_telegram
  ```

+ **Worker ARQ:**
+ ```bash
+ python -m src.worker_arq.bot_worker
+ ```
```

**Обоснование:**
- Новые разработчики сразу увидят требование настройки PYTHONPATH
- Инструкции для разных IDE и ОС
- Правильные команды запуска для всех сервисов

---

## Дополнения к template (опционально)

### 1. Создать `.vscode/settings.json` в template

**Файл:** `.vscode/settings.json` (создать новый)

```json
{
    "python.analysis.extraPaths": ["${workspaceFolder}"],
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}"
    },
    "terminal.integrated.env.osx": {
        "PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}"
    },
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder};${env:PYTHONPATH}"
    },
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },
    "python.analysis.typeCheckingMode": "basic"
}
```

**Обоснование:**
- VSCode пользователи получат правильную конфигурацию "из коробки"
- Автоматическая настройка PYTHONPATH в терминале
- Интеграция с Ruff и форматированием

---

### 2. Добавить `.gitignore` запись для `.vscode`

**Файл:** `.gitignore`

```diff
+ # IDE
+ .vscode/
+ .idea/
```

Или, если хотите коммитить settings:
```diff
+ # IDE
+ .vscode/*
+ !.vscode/settings.json
+ .idea/
```

---

## Особенности lily_website (НЕ применять в template)

Следующие изменения специфичны для lily_website и **НЕ ДОЛЖНЫ** применяться в базовом template:

### 1. Worker ARQ структура

В lily_website Worker был вынесен в отдельную папку `src/worker_arq/`:

```
lily_website/
├── src/
│   ├── backend_django/
│   ├── telegram_bot/
│   ├── worker_arq/          ← Новая структура!
│   │   ├── __init__.py
│   │   ├── bot_worker.py
│   │   └── tasks/
│   └── shared/
```

**В базовом template Worker находится в:**
```
template/
├── src/
│   ├── telegram_bot/
│   │   └── services/
│   │       └── worker/      ← Исходная структура
│   │           ├── __init__.py
│   │           └── bot_worker.py
```

**Действие для template:**
- ✅ Применить PYTHONPATH исправления
- ❌ НЕ менять структуру папок Worker
- ✅ Обновить `deploy/worker/Dockerfile` с учетом старой структуры

---

### 2. Другие специфичные изменения lily_website

- Redis Streams для коммуникации Django ↔ Bot
- Booking система с wizard
- Множественные языки (i18n)
- Кастомные миграции и фикстуры

**Действие для template:**
Не копировать эти изменения, они не относятся к проблемам с PYTHONPATH.

---

## Чек-лист для применения в template

### Подготовка

- [ ] Создать новую ветку в template репозитории: `fix/pythonpath-structure`
- [ ] Открыть этот документ для справки

### Применение исправлений (по порядку)

- [ ] **1. Backend Dockerfile** (`deploy/backend/Dockerfile`)
  - [ ] Строка 20: Изменить PYTHONPATH на `/app:$PYTHONPATH`
  - [ ] Строка 23: Добавить `cd /app/src/backend_django &&` перед collectstatic

- [ ] **2. docker-compose.yml** (`deploy/docker-compose.yml`)
  - [ ] Строка 7: Обновить command на `python src/backend_django/manage.py runserver`
  - [ ] Строки 13-14: Исправить volumes для backend:
    - `../src/backend_django:/app/src/backend_django`
    - `../src/shared:/app/src/shared:ro`

- [ ] **3. Bot Dockerfile** (`deploy/bot/Dockerfile`)
  - [ ] После строки 17: Добавить `ENV PYTHONPATH="/app:$PYTHONPATH"`

- [ ] **4. Worker Dockerfile** (`deploy/worker/Dockerfile`)
  - [ ] После строки 16: Добавить `ENV PYTHONPATH="/app:$PYTHONPATH"`
  - [ ] ⚠️ Проверить CMD — должен использовать путь из template (НЕ из lily_website)

- [ ] **5. CI/CD workflows** (`.github/workflows/cd-release.yml`)
  - [ ] Строка 42: Исправить путь Worker Dockerfile на `deploy/worker/Dockerfile`
  - [ ] Строки 75-76: Добавить `src/backend_django/` в пути к manage.py

- [ ] **6. pytest конфигурация** (`pyproject.toml`)
  - [ ] После строки 91: Добавить `pythonpath = ["."]`

- [ ] **7. README.md** (`README.md`)
  - [ ] Добавить секцию "Python Path Configuration"
  - [ ] Обновить команды запуска сервисов
  - [ ] Добавить инструкции для PyCharm и VSCode

- [ ] **8. VSCode settings** (опционально)
  - [ ] Создать `.vscode/settings.json`
  - [ ] Обновить `.gitignore` для `.vscode/`

### Тестирование

- [ ] **Локальная разработка**
  - [ ] Установить PYTHONPATH согласно README
  - [ ] `cd src/backend_django && python manage.py check` — без ошибок
  - [ ] `python -m src.telegram_bot.app_telegram --help` — без ошибок
  - [ ] `pytest src/` — тесты находят модули

- [ ] **Docker development**
  - [ ] `cd deploy && docker-compose build --no-cache`
  - [ ] `docker-compose up`
  - [ ] Проверить логи всех сервисов (backend, bot, worker) — нет `ModuleNotFoundError`
  - [ ] Backend доступен на http://localhost:8000
  - [ ] Зайти в контейнер: `docker exec -it <backend_container> python -c "from src.shared.core.config import CommonSettings; print('OK')"`

- [ ] **Docker production build**
  - [ ] `docker-compose -f docker-compose.prod.yml build --no-cache`
  - [ ] `docker-compose -f docker-compose.prod.yml up -d`
  - [ ] Миграции проходят без ошибок
  - [ ] collectstatic выполняется без ошибок

- [ ] **CI/CD** (если есть тестовый деплой)
  - [ ] Запустить GitHub Actions workflow
  - [ ] Проверить что все шаги проходят без ошибок
  - [ ] Деплой на test сервер успешен

### Финализация

- [ ] Коммит изменений с детальным сообщением
- [ ] Создать Pull Request в template репозитории
- [ ] Добавить этот документ (TEMPLATE_IMPROVEMENTS.md) в PR description
- [ ] Code review с командой
- [ ] Мержить в main ветку template
- [ ] Обновить CHANGELOG template
- [ ] Создать Git tag для новой версии template (например, `v1.1.0`)

---

## Проверка совместимости

После применения всех исправлений, проект должен работать во всех режимах:

| Режим | Проверка | Ожидаемый результат |
|-------|----------|---------------------|
| Локально (Linux/macOS) | `export PYTHONPATH=$(pwd) && pytest src/` | Все тесты проходят |
| Локально (Windows) | `$env:PYTHONPATH = "$PWD"; pytest src/` | Все тесты проходят |
| Docker dev | `docker-compose up` | Все сервисы запускаются без ошибок импорта |
| Docker prod | `docker-compose -f docker-compose.prod.yml up` | Деплой успешен, миграции выполнены |
| CI/CD | GitHub Actions workflow | Все шаги проходят, образы собираются |
| IDE (PyCharm) | Open project, mark root as Source | Автокомплит работает для `src.shared` |
| IDE (VSCode) | Open project with `.vscode/settings.json` | Pylance находит все импорты |

---

## Заключение

Основная проблема заключалась в несогласованности между:
1. Путями где находятся файлы (`/app/src/shared`)
2. PYTHONPATH который указывал на другие пути (`/app/shared`)
3. Способами монтирования в docker-compose (backend vs bot/worker)

**Решение:** Унифицировать все на использование `/app` как корня PYTHONPATH и `/app/src/` как структуры проекта.

Это минимальное изменение, которое:
- ✅ Не требует изменения кода
- ✅ Не требует изменения импортов
- ✅ Работает во всех окружениях одинаково
- ✅ Следует Python best practices для монорепо

---

## Контакты и вопросы

При применении этих исправлений в template, если возникнут вопросы:

1. Обратиться к автору этого отчета
2. Проверить план реализации: [expressive-noodling-flamingo.md](C:\Users\prime\.claude\plans\expressive-noodling-flamingo.md)
3. Открыть Issue в template репозитории с тегом `pythonpath-fix`

---

**Конец отчета**

Дата создания: 2026-02-12
Версия: 1.0
Статус: Готов к применению в template
