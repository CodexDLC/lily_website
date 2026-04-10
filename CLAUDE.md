# CLAUDE.md — lily_website

> Читать в начале каждой сессии. Ориентация по проекту, памяти и архитектурным решениям.

---

## Расположение проекта

```
C:\install\projects\clients\lily_website\
```

Зависит от библиотек из:
```
C:\install\projects\codex_tools\
  codex-django\      ← библиотека кабинета
  codex-core\
  codex-services\
```

---

## MCP Граф памяти — навигация

Сервер: `memory` (MCP)

```python
# Старт навигации всегда с:
search_nodes("MASTER_INDEX")
```

### Глобальные индексы

| Нода | Содержит |
|------|---------|
| `MASTER_INDEX` | 7 секций (SEC:*) — главная точка входа |
| `AI_PRIVATE_INDEX` | Черновики и временные заметки AI-агента |
| `Graph:ConventionStandard` | Правила именования нод, типы связей |

### Секции MASTER_INDEX

| Нода | Тема |
|------|------|
| `SEC:Ecosystem` | Обзор всех codex-* проектов |
| `SEC:Libraries` | Детальные индексы библиотек |
| `SEC:Architecture` | Архитектурные решения codex-django |
| `SEC:Standards` | Протоколы и конвенции |
| `SEC:Skills` | Навыки и инструменты AI-агента |
| `SEC:Methodology` | Паттерны разработки |
| `SEC:User` | Предпочтения пользователя |

---

## codex-django кабинет — подграф памяти

Входная точка: **`codex-django:cabinet:index`**
Все дочерние ноды имеют префикс `codex-django:cabinet:`.

| Нода | Тип | Что описывает |
|------|-----|--------------|
| `codex-django:cabinet:index` | project-index | Мастер-индекс. Two-space модель, declare() API, файловая структура |
| `codex-django:cabinet:registry` | Component | Singleton-реестр. V1/V2 API, `declare()` роутинг |
| `codex-django:cabinet:autodiscover` | Mechanism | Boot: `CabinetConfig.ready()` → `autodiscover_modules('cabinet')` |
| `codex-django:cabinet:context-pipeline` | Component | Context processors: space/module detection, permissions, sidebar/topbar |
| `codex-django:cabinet:content-components` | Component | DataTable, CalendarGrid, CardGrid, ListView, SplitPanel |
| `codex-django:cabinet:modal-system` | Component | Modal dispatch, generic_modal.html, 7 section types |
| `codex-django:cabinet:dashboard` | Component | DashboardSelector, @extend decorator, Redis кэш, widget templates |
| `codex-django:cabinet:site-settings` | Component | Auto-tab discovery via `_*.html` partials |
| `codex-django:cabinet:notifications` | Component | NotificationRegistry, @register('key') pattern, bell providers |
| `codex-django:cabinet:satellite-modules` | Component | booking/cabinet, conversations/cabinet, system/cabinet |
| `codex-django:cabinet:css-js` | conventions | CSS/JS стек, компилер, load order |

### Навигация по подграфу

```
codex-django:cabinet:index
  HAS_COMPONENT → registry
  HAS_COMPONENT → autodiscover → POPULATES → registry
  HAS_COMPONENT → context-pipeline → READS → registry + notifications
  HAS_COMPONENT → dashboard → USES → registry
  HAS_COMPONENT → modal-system → DISPATCHED_FROM → content-components
  HAS_COMPONENT → satellite-modules → REGISTERS_IN → registry + notifications
  HAS_COMPONENT → site-settings
  HAS_COMPONENT → content-components
  HAS_COMPONENT → notifications
  DEFINES_CONVENTION → css-js
```

---

## Снимки кодовой базы в памяти

| Нода | Тип | Тема |
|------|-----|------|
| `lily_2x_library` | library_snapshot | codex-django v0.2.7+: booking, notifications, system, core модули |
| `lily_2x_new_scaffold` | codebase_snapshot | Текущий проект (`src/lily_backend/`): что реализовано, что нет |
| `lily_2x_old_backend` | codebase_snapshot | Старый backend (`src/backend_django/`): reference-only |

---

## Ключевые архитектурные паттерны

### Two-space модель кабинета

| Space | URL prefix | Base template |
|-------|-----------|---------------|
| `staff` | `/cabinet/` | `base_cabinet.html` |
| `client` | `/cabinet/my/` | `base_client.html` |

### declare() API (в каждом feature-app)

```python
# features/booking/cabinet.py
from codex_django.cabinet import declare, TopbarEntry, SidebarItem

declare(
    space="staff",
    module="booking",
    topbar=TopbarEntry(group="services", label="Booking", icon="bi-calendar", url="/cabinet/booking/"),
    sidebar=[SidebarItem(label="Расписание", url="booking:schedule", icon="bi-calendar3")],
)
declare(space="client", module="booking", sidebar=[SidebarItem(...)])
```

### View pattern

```python
# В любом view кабинета:
request.cabinet_module = "booking"  # context processor возьмёт sidebar для этого модуля
```

---

## Локальная документация (codex-django проект)

Путь: `C:\Users\prime\.claude\projects\C--install-projects-codex-tools-codex-django\memory\`

| Файл | Тема |
|------|------|
| `MEMORY.md` | Мастер-индекс локальных файлов |
| `cabinet_index.md` | Cabinet 2.0: типы, компоненты, шаблоны, API |
| `cabinet_css_js.md` | CSS/JS стек, load order, compiler_config.json |
| `cabinet_dashboard_architecture.md` | DashboardSelector, Redis, adapter pattern |
| `roadmap_overview.md` | 8 блоков доделки, статусы |

---

## Как стартовать новую сессию

1. Прочитай этот файл
2. `search_nodes("MASTER_INDEX")` — навигация по экосистеме
3. `search_nodes("codex-django:cabinet:index")` — контекст кабинета
4. `search_nodes("lily_2x_new_scaffold")` — статус текущего проекта
5. При работе с кабинетом: ищи ноды с префиксом `codex-django:cabinet:`
