# Задача: Исправление невалидных элементов структурированных данных (Invalid structured data items)

- Режим: с ревизором
- Состояние: accepted
- Рабочий каталог / ветка / исходное состояние: `D:\Workspace\clients\lily_website`, branch: main
- Выбор режима пользователем: «с независимым» — изолированный агент task-reviewer выполнил независимую верификацию синтаксиса и схемы JSON-LD на всех языках.

## Исходное задание и уточнения

1. Запрос пользователя:
   - Сообщение 1: Список проблем Semrush, включая «Invalid structured data items [4 pages] (https://www.semrush.com/siteaudit/campaign/31563261/review/issue/detail/45) How to fix».
   - Выбор режима: «с не зависимым» для исправления структурированных данных.

## Требования и ограничения

- [x] R1: В шаблонах microdata/JSON-LD (`_schema_home_page.html`, `_schema_contact_page.html`, `_schema_local_business.html`) нормализовать свойство `openingHours`: не передавать дни со значением «Geschlossen» / пустые строки (например, `"Su Geschlossen"`, `"Mo-Fr "`), форматировать рабочие интервалы по стандарту Schema.org.
- [x] R2: В `_schema_contact_page.html` исправить обращение к контексту: заменить ошибочный `settings.*` на `site_settings.*`, убрать некорректно вложенные теги `{% block title %}` и `{% block meta_description %}` из содержимого JSON-LD, гарантировать вывод телефона, email, адреса организации.
- [x] R3: В `_schema_home_page.html` и связанных схемах формировать корректные абсолютные URL для `image` (без относительных путей), убирать блок `geo` (GeoCoordinates) если координаты не заданы (не передавать пустые строки `""`), нормализовать `@id` организации.
- [x] R4: В `_schema_service_detail.html` исправить невалидное свойство `"hasOffer"` на стандартное Schema.org `"offers"`, исправить дублирование базового URL в пути к изображению услуги.
- [x] R5: В `base.html` подключить блок `{% block extra_head_schema %}{% endblock %}`, чтобы дочерние шаблоны (в частности, FAQ c `FAQPage`) могли передавать валидные структурированные данные в `<head>`.
- [x] R6: Обеспечить синтаксическую валидность JSON и соответствие Schema.org на всех 4 языках (`de`, `en`, `ru`, `uk`) для главной страницы, контактов, услуг и FAQ.

## Предположения и открытые вопросы

- Используется формат JSON-LD (`application/ld+json`).
- Воскресенье в салоне является нерабочим днем («Geschlossen»), поэтому в `openingHours` должны попадать только открытые дни (Mo-Fr, Sa).

## План реализации

1. Исправить `src/lily_backend/templates/features/main/_schema_home_page.html`:
   - Отфильтровать `openingHours`: выводить только непустые и открытые дни (без "Geschlossen").
   - Обеспечить абсолютный URL логотипа через `CANONICAL_BASE_URL` или `site_settings.site_base_url`.
   - Проверять наличие координат перед выводом секции `geo`.
2. Исправить `src/lily_backend/templates/features/conversations/_schema_contact_page.html`:
   - Заменить `settings.*` на `site_settings.*`.
   - Убрать теги `{% block title %}` внутри JSON.
   - Отфильтровать нерабочие дни в `openingHours`.
3. Исправить `src/lily_backend/templates/features/main/services/_schema_service_detail.html`:
   - Заменить `"hasOffer"` на `"offers"`.
   - Исправить `image`: не дублировать `request.build_absolute_uri` с абсолютным или относительным url изображения.
4. Исправить `src/lily_backend/templates/includes/_schema_local_business.html`:
   - Привести к единому стандарту `openingHours`, `image`, `geo`.
5. В `src/lily_backend/templates/base.html`:
   - Добавить `{% block extra_head_schema %}{% endblock %}` в секцию `<head>`.
6. Проверить генерацию JSON-LD скриптом верификации на валидность JSON и Schema.org (Home, Contacts, Services, FAQ на DE, EN, RU, UK).

## Журнал уточнений

- 2026-10-20 — Пользователь выбрал режим с независимым ревизором для задачи Invalid structured data items.

## Выполнение и доказательства

| ID | Реализация pending/done | Проверка pending/pass/partial/fail/unverified и кто проверял | Доказательство и состояние результата |
| --- | --- | --- | --- |
| R1 | done | pass (ревизор: task-reviewer `pro`) | `openingHours` в `_schema_home_page.html`, `_schema_contact_page.html`, `_schema_local_business.html` фильтрует нерабочие дни и пустые значения; для воскресенья («Geschlossen») исключена невалидная строка; интервалы отформатированы как `HH:MM-HH:MM`. |
| R2 | done | pass (ревизор: task-reviewer `pro`) | В `_schema_contact_page.html` исправлено обращение к `site_settings.*`, убраны некорректные теги `{% block %}`, телефон, email и адрес выводятся с дефолтными значениями при отсутствии в БД. |
| R3 | done | pass (ревизор: task-reviewer `pro`) | `image` везде генерирует абсолютные URL с `CANONICAL_BASE_URL`; секция `geo` выводится только при наличии координат (устранены пустые строки в `GeoCoordinates`); `@id` стандартизирован как `{{ CANONICAL_BASE_URL }}/#organization`. |
| R4 | done | pass (ревизор: task-reviewer `pro`) | В `_schema_service_detail.html` свойство `"hasOffer"` заменено на стандартное Schema.org `"offers"`, устранен двойной URL в `image`. |
| R5 | done | pass (ревизор: task-reviewer `pro`) | В `base.html` добавлен `{% block extra_head_schema %}{% endblock extra_head_schema %}`. В `faq.html` разметка `FAQPage` успешно выводится в `<head>` с 9 парами Question/Answer на всех языках. |
| R6 | done | pass (ревизор: task-reviewer `pro`) | Автономный проверочный скрипт ревизора протестировал 36 реальных маршрутов на 4 языках (DE, EN, RU, UK): 36/36 валидных JSON-LD блоков, 0 синтаксических ошибок, 0 нарушений схемы Schema.org. |

## Независимая ревизия

- Субагент: `task-reviewer` (модель уровня `pro`, conversation ID: `72425125-cfef-4fd5-b476-f02dc855e8c7`).
- Вердикт: R1–R6: **PASS** (100% подтверждение). Все 6 утверждений отчёта исполнителя признаны достоверными и подтверждены независимой проверкой.

## Разбор замечаний

Замечаний и дефектов не выявлено.

## Принятие пользователем

Принято пользователем (2026-10-20): 100% валидность структурированных данных подтверждена независимым ревизором. Задача переведена в статус `accepted`.
