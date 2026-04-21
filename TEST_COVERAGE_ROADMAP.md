# План: поднятие покрытия тестами src/ с 46.53% до ≥90%

## Context

Текущее покрытие — 46.53% при пороге 90% (fail). Большая часть «дыры» приходится не на лёгкий boilerplate, а на **боевой код**: booking engine (cabinet.py 41%, runtime.py 33%), публичная воронка бронирования (cart/commit/wizard ~15–53%), workers (dual-provider notifications 0–16%), Telegram-бот (0%). Цель — не снижать порог, а покрыть src/ реально, разделив тесты на три уровня:

- **unit** — с моками, fakeredis, sqlite in-memory.
- **integration** — sqlite + fakeredis + Django TestClient, без внешних систем.
- **e2e** — внутри docker-compose стенда (Postgres + Redis + backend + bot + workers + Mailpit для почты).

Отдельно — честный аудит того, что можно и нужно исключить из `coverage.omit` как легитимный glue.

---

## 1. Categorization по критичности

### 🔴 RED — критично, покрываем в первую очередь (revenue / customer-impacting)

| Путь | LoC | Cov | Почему |
| :--- | :--- | :--- | :--- |
| `src/lily_backend/features/booking/services/cabinet.py` | 301 | 96% | Главный оркестратор cabinet booking. [DONE] |
| `src/lily_backend/features/booking/providers/runtime.py` | 162 | 91% | ORM-провайдер availability — ядро движка. [DONE] |
| `src/lily_backend/features/booking/views/public/cart.py` | 113 | 100% | Публичная воронка — корзина услуг. [DONE] |
| `src/lily_backend/features/booking/views/public/commit.py` | 109 | 94% | Публичная воронка — подтверждение брони. [DONE] |
| `src/lily_backend/features/booking/views/public/wizard.py` | 32 | 100% | Публичная воронка — многошаговый мастер. [DONE] |
| `src/lily_backend/features/booking/views/public/scheduler.py` | 124 | 98% | Публичная воронка — выбор слотов. [DONE] |
| `src/lily_backend/features/booking/selector/engine.py` | 135 | 67% | Алгоритм подбора мастера/слота. |
| `src/lily_backend/features/booking/dto/public_cart.py` | 74 | 74% | DTO публичной корзины. |
| `src/workers/core/base_module/orchestrator.py` | 35 | 0% | Fallback между провайдерами уведомлений. |
| `src/workers/core/base_module/email_client.py` | 62 | 16% | SMTP → SendGrid fallback. |
| `src/workers/core/base_module/twilio_service.py` | 89 | 0% | Twilio SMS/WA. |
| `src/workers/core/base_module/seven_io_client.py` | 39 | 0% | Seven.io SMS. |
| `src/workers/notification_worker/tasks/notification_tasks.py` | 161 | 40% | Подтверждения/напоминания бронирований. |
| `src/workers/notification_worker/tasks/email_tasks.py` | 30 | 0% | Отправка email. |
| `src/workers/notification_worker/tasks/message_tasks.py` | 50 | 0% | Отправка SMS/WA. |
| `src/workers/notification_worker/dependencies.py` | 75 | 0% | DI воркера. |
| `src/lily_backend/features/conversations/services/notifications.py` | 111 | 100% | Универсальный event-dispatcher уведомлений. [DONE] |

### 🟡 YELLOW — важно, второй приоритет (staff workflow, data integrity)

| Путь | LoC | Cov | Почему |
| :--- | :--- | :--- | :--- |
| `src/lily_backend/cabinet/services/analytics.py` | 127 | 100% | Staff dashboard KPI. [DONE] |
| `src/lily_backend/cabinet/services/booking.py` | 68 | 49% | Cabinet booking modal contracts. |
| `src/lily_backend/cabinet/services/client.py` | 108 | 57% | Client cabinet view-model. |
| `src/lily_backend/cabinet/services/conversations.py` | 92 | 95% | Cabinet conversations view-model. [DONE] |
| `src/lily_backend/cabinet/services/users.py` | 48 | 100% | Staff users list. [DONE] |
| `src/lily_backend/cabinet/views/*` (booking, client, conversations, staff, ops, services) | ~500 | 25–71% | HTTP-контракты кабинета. |
| `src/lily_backend/features/conversations/services/alerts.py` | 61 | 52% | Staff alerts. |
| `src/lily_backend/features/conversations/services/workflow.py` | 64 | 50% | Переходы статусов. |
| `src/lily_backend/features/conversations/services/email_import.py` | 33 | 64% | IMAP polling. |
| `src/lily_backend/features/conversations/views/contact.py` | 44 | 30% | Форма контакта. |
| `src/workers/system_worker/tasks/email_import.py` | 182 | 92% | IMAP → conversations pipeline. [DONE] |
| `src/workers/system_worker/tasks/booking.py` | 29 | 100% | Maintenance задачи. [DONE] |
| `src/workers/system_worker/tasks/tracking.py` | 31 | 100% | Tracking flush. [DONE] |
| `src/workers/system_worker/dependencies.py` | 16 | 100% | DI воркера. [DONE] |
| `src/lily_backend/system/selectors/masters.py` | 54 | 20% | Queryset мастеров. |
| `src/lily_backend/system/services/worker_ops.py` | 107 | 89% | Операции воркеров. |
| `src/workers/core/heartbeat.py` | 54 | 100% | Heartbeat registry. [DONE] |
| `src/telegram_bot/features/redis/notifications/logic/booking_processor.py` | 93 | 0% | Преобразование booking-уведомлений в TG-UI. |
| `src/telegram_bot/features/redis/notifications/logic/contact_processor.py` | 33 | 0% | Обработка контакт-уведомлений. |
| `src/telegram_bot/services/redis/dispatcher.py` | 57 | 0% | Роутинг Redis Stream → aiogram. |
| `src/telegram_bot/services/redis/stream_processor.py` | 64 | 0% | Чтение Redis Stream. |
| `src/telegram_bot/middlewares/*` | ~100 | 0% | i18n, security, throttling, user_validation. |

### 🟢 GREEN — низкая ценность покрытия (исключаем из coverage или допускаем 0%)

Предлагаю расширить `pyproject.toml [tool.coverage.run] omit` следующими путями (все — entry points, glue, config):

```toml
omit = [
    # уже есть:
    "*/migrations/*", "*/tests/*", "*/conftest.py", "*/manage.py",
    "*/wsgi.py", "*/asgi.py", "*/settings/*", "*/fixtures/*",
    "*/management/commands/*", "*/admin.py", "*/apps.py",
    "*/translation.py", "*/core/sitemaps.py", "*/signals.py",
    # добавить:
    "src/telegram_bot/app_telegram.py",                  # bot bootstrap
    "src/telegram_bot/core/config.py",                   # pydantic settings
    "src/telegram_bot/core/factory.py",                  # aiogram glue
    "src/telegram_bot/core/routers.py",                  # include_router glue
    "src/telegram_bot/core/container.py",                # DI container wiring
    "src/telegram_bot/core/logger.py",                   # loguru setup
    "src/telegram_bot/core/settings.py",                 # config façade
    "src/telegram_bot/core/garbage_collector.py",        # gc hook
    "src/telegram_bot/core/api_client.py",               # тонкий httpx wrapper (если нет логики)
    "src/telegram_bot/features/*/feature_setting.py",    # декларативная регистрация feature
    "src/telegram_bot/features/*/resources/keyboards.py",# aiogram keyboards (декларативно)
    "src/telegram_bot/features/*/resources/texts.py",    # строковые константы
    "src/telegram_bot/features/*/resources/callbacks.py",# callback_data классы
    "src/telegram_bot/features/*/ui/*",                  # UI-рендеринг сообщений
    "src/telegram_bot/infrastructure/redis/container.py",
    "src/telegram_bot/infrastructure/models/base.py",
    "src/telegram_bot/resources/*",                      # constants, states
    "src/lily_backend/core/logger.py",                   # loguru setup
    "src/lily_backend/core/urls.py",                     # routing
    "src/lily_backend/*/urls.py",                        # все Django urls
    "src/workers/notification_worker/worker.py",         # arq bootstrap
    "src/workers/system_worker/worker.py",               # arq bootstrap
    "src/workers/notification_worker/config.py",
    "src/workers/system_worker/config.py",
    "src/workers/core/config.py",                        # pydantic settings
    "src/workers/core/tasks.py",                         # arq task registry glue
    "src/workers/core/base.py",                          # base classes
    "src/workers/*/tasks/task_aggregator.py",            # task list aggregator
]
```

**Обоснование:** это реально декларативный/bootstrap-код. Оценка удаления: закроет ~900–1200 непокрытых строк без потери инвариантов, так как эти модули тестируются неявно через e2e.

---

## 2. Тестовая стратегия (три уровня)

### Level 1 — Unit (pytest, fakeredis, sqlite in-memory, mocks)

**Стек:** pytest, pytest-django, pytest-asyncio, `fakeredis` (добавить в dev-группу), `freezegun`, `pytest-mock`, `responses` для httpx/requests.

**Покрываем:**
- Чистые функции: `selector/engine.py`, `dto/public_cart.py`, `booking_settings.py`.
- Service-слой без I/O или с замоканным I/O: `features/booking/services/*`, `cabinet/services/*`, `conversations/services/notifications.py`.
- Провайдеры `runtime.py` на sqlite с фикстурами (Master, Service, WorkingDay).
- Workers: `notification_worker/tasks/*` с fakeredis + замоканными SMTP/Twilio/Seven.io клиентами.
- Telegram bot: `booking_processor`, `dispatcher`, middlewares — с MagicMock Bot/Dispatcher (aiogram поддерживает `MemoryStorage`).

**Fixtures (tests/conftest.py + tests/fixtures/):**
- `fakeredis_client` (уже есть частично) — расширить.
- `db` — sqlite, миграции прогоняются автоматически.
- `booking_factory`, `master_factory`, `client_factory`, `appointment_factory` (factory_boy — добавить).
- `mock_smtp`, `mock_twilio`, `mock_seven_io` — responses/httpx_mock.
- `frozen_time` — freezegun.

### Level 2 — Integration (тот же процесс, но несколько компонентов вместе)

**Покрываем:**
- Django views + service + ORM (sqlite): публичная воронка `views/public/*` — полные HTTP-сценарии через Django test client.
- Worker task → DB → notification dispatch (fakeredis).
- Cabinet views + service + ORM — staff flow (create → edit → cancel).
- Conversations: email import → message → alert (IMAP замокан).

**Marker:** `@pytest.mark.integration`. Запуск: `pytest -m integration`.

### Level 3 — E2E (docker-compose, Postgres, Redis, Mailpit)

**Инфраструктура:**
- Новый файл `deploy/docker-compose.test.yml` с сервисами: `postgres`, `redis`, `mailpit` (SMTP+web UI для проверки писем), `backend`, `telegram_bot` (в режиме polling + мокнутый TG API через локальный stub), `notification_worker`, `system_worker`.
- Новая директория `tests/e2e/` с marker `@pytest.mark.e2e`.
- Запуск: `docker compose -f deploy/docker-compose.test.yml up -d && pytest -m e2e`.

**Покрываем:**
- Booking public funnel end-to-end: создание appointment → публикация в Redis Stream → worker отправляет e-mail → Mailpit API проверяет, что письмо ушло.
- Cabinet action token flow: reschedule token → Redis → Django view → подтверждение.
- IMAP import: локальный inbox (Mailpit умеет принимать SMTP) → system_worker → message в DB.
- Telegram notification: Redis Stream → stub TG API (заменяем `bot.send_message` на локальный HTTP-recorder).

**Что остаётся на e2e (не тянется в sqlite/fakeredis):**
- Реальная Postgres-специфика: FTS, партиционирование, индексы, транзакционная изоляция при гонках.
- Arq-воркеры в живом процессе (timeout, retry).
- Redis Streams consumer groups (fakeredis поддерживает streams не полностью).
- Aiogram live polling (только smoke).

---

## 3. Этапы внедрения

### Этап 0 — Инфраструктура тестов (≈ 1 день) — [x] DONE
1. [x] В `pyproject.toml [dependency-groups].dev` добавить: `fakeredis`, `freezegun`, `factory-boy`, `pytest-mock`, `responses`, `pytest-httpx`.
2. [x] Расширить `omit` в coverage (см. секцию 1-GREEN).
3. [x] Добавить markers: `e2e` в `pyproject.toml`.
4. [x] Разделить `tests/` на `tests/unit/`, `tests/integration/`, `tests/e2e/` (сохранить существующие подпапки по доменам).
5. [x] Создать базовые фикстуры: `tests/conftest.py` — `fakeredis_client`, `factory_boy` фабрики в `tests/factories/`.
6. [x] CI: добавить job `test-unit` (быстрый, без докера), `test-integration` (быстрый), `test-e2e` (docker compose up).

**Verify:** `pytest -m "not e2e"` проходит, `pytest --collect-only` показывает правильные markers.

### Этап 1 — RED тир, booking core (≈ 3–4 дня) — [x] DONE
Файлы:
- `src/lily_backend/features/booking/providers/runtime.py` — unit на sqlite. (**91%**)
- `src/lily_backend/features/booking/services/cabinet.py` — unit + integration (cabinet view). (**96%**)
- `src/lily_backend/features/booking/views/public/{cart,commit,scheduler,wizard}.py` — integration через Django test client. (**94-100%**)
- `src/lily_backend/features/booking/selector/engine.py` — unit (есть частичное покрытие). (**100%**)
- `src/lily_backend/features/booking/dto/public_cart.py` — unit (pure). (**100%**)

**Сценарии:** доступные слоты (day/week), конфликты услуг, свойства мастера, группы appointments, перепланирование, отмена, лимиты, edge cases (overlapping → уже есть тест, расширить).

**Target cov:** RED-booking ≥ 85%. (**Done: 94-100%**)

### Этап 2 — RED тир, workers / notifications (≈ 3 дня) — [/] IN PROGRESS
Файлы:
- `src/workers/core/base_module/{orchestrator,email_client,twilio_service,seven_io_client,template_renderer}.py` — unit с httpx_mock / aiosmtplib mock.
- `src/workers/notification_worker/tasks/{notification_tasks,email_tasks,message_tasks}.py` — unit с fakeredis + мокнутым orchestrator.
- `src/workers/notification_worker/dependencies.py` — smoke.
- `src/lily_backend/features/conversations/services/notifications.py` — unit.

**Сценарии:** primary success, primary fail → fallback success, both fail → retry, template rendering (placeholders, i18n), duplicate-guard через Redis.

**Target cov:** RED-workers ≥ 85%.

### Этап 3 — YELLOW тир, cabinet + conversations (≈ 3 дня) — [/] IN PROGRESS
Файлы: `cabinet/services/*`, `cabinet/views/*`, `conversations/services/{alerts,workflow,email_import}.py`, `conversations/views/contact.py`, `system_worker/tasks/{email_import,booking}.py`.

**Сценарии:** KPI dashboard расчёты, client view, staff roster, email import парсинг, alert dispatch, form validation.

**Target cov:** YELLOW ≥ 75%.

### Этап 4 — Telegram bot (≈ 2–3 дня)
Файлы: `telegram_bot/features/redis/notifications/logic/*`, `services/redis/{dispatcher,stream_processor,router}.py`, `middlewares/*`, `services/director/director.py`, `services/fsm/*`, `services/url_signer/service.py`, `infrastructure/api_route/appointments.py`.

**Сценарии:** Redis Stream → processor → TG bot (замокан), middleware блокировки, FSM переходы, подпись URL. Использовать aiogram `Dispatcher` + `MemoryStorage` + `MockedBot`.

**Target cov:** покрываемые файлы ≥ 70% (UI/keyboards/texts — в omit, поэтому не учитываются).

### Этап 5 — E2E сборка (≈ 2 дня)
1. `deploy/docker-compose.test.yml` с Postgres, Redis, Mailpit, backend, bot, 2 воркера.
2. `tests/e2e/conftest.py` — fixture `live_stack`, `mailpit_client` (HTTP API `http://mailpit:8025/api/v1/messages`), `redis_live`, `tg_api_stub`.
3. Ключевые сценарии:
   - публичная бронь → письмо клиенту (проверка в Mailpit);
   - cabinet reschedule → action-token redis → письмо-подтверждение;
   - contact form → alert staff (TG stub + email в Mailpit);
   - email import: SMTP send в Mailpit → IMAP pull (или HTTP API Mailpit как источник) → `ConversationMessage` создан.
4. CI job: `docker compose up -d && pytest -m e2e && docker compose down -v`.

**Target cov:** добавляет +3–5% к общему (через интеграционные пути, которые unit не ловит).

### Этап 6 — Финальный прогон и снижение порога по секциям (≈ 1 день)
1. Проверить общий `coverage` ≥ 90% (цель для Unit-слоя).
2. Разделить запуск в CI:
   - Unit: `pytest -m "unit or not integration" --cov=src --cov-fail-under=90` (строгий гейт).
   - Integration: `pytest -m "integration" --no-cov` (без гейта, для верификации сценариев).
3. Если не добираем — точечно дописать тесты в YELLOW; **порог не снижаем**.

---

## 4. Критические файлы для правки

| Путь | Правка |
|------|--------|
| `pyproject.toml` | Добавить dev-deps, расширить `coverage.omit`, добавить `e2e` marker. |
| `tests/conftest.py` | `fakeredis_client`, `factory_boy` фикстуры. |
| `tests/factories/` (новый) | ModelFactory для Master, Service, Appointment, Client, Conversation. |
| `tests/unit/`, `tests/integration/`, `tests/e2e/` | Реорганизация. |
| `deploy/docker-compose.test.yml` (новый) | Стенд для e2e с Mailpit. |
| `.github/workflows/*` или `tools/dev/check.py` | Добавить стадии unit/integration/e2e. |

**Переиспользовать:**
- Существующие tests под `tests/lily_backend/unit/` и `tests/lily_backend/integration/` — не ломать, достроить.
- `tests/conftest.py` уже мокает redis sync calls — расширить, не переписывать.

---

## 5. Verification (как проверим end-to-end)

1. `uv run pytest -m unit` — зелёный, быстрый (<30 сек).
2. `uv run pytest -m integration` — зелёный, sqlite+fakeredis (<2 мин).
3. `docker compose -f deploy/docker-compose.test.yml up -d --wait && uv run pytest -m e2e` — зелёный (<5 мин).
4. `uv run pytest` без marker-фильтра — overall coverage ≥ 90%, HTML-отчёт в `htmlcov/`.
5. `tools/dev/check.py` прогон — pre-commit + unit + integration зелёные.
6. Ручная проверка Mailpit UI (`http://localhost:8025`) во время e2e: письма действительно приходят.

---

## 6. Отчёт для проекта

После одобрения этого плана я сохраню **этот же документ** в корень репозитория как `TEST_COVERAGE_ROADMAP.md` (plan-режим запрещает писать туда сейчас), чтобы он был под контролем версий и доступен команде.

---

## Сводка приоритетов

| Тир | Файлов | Ожидаемый вклад в cov | Срок |
|-----|--------|----------------------|------|
| Инфраструктура | — | — | 1 д |
| RED booking | ~8 | +18% | 3–4 д |
| RED workers | ~8 | +12% | 3 д |
| YELLOW cabinet/conv | ~20 | +10% | 3 д |
| Telegram | ~15 | +5% | 2–3 д |
| E2E | — | +4% | 2 д |
| **Итого** | — | **46% → 90%+** | **~14–16 дней** |
