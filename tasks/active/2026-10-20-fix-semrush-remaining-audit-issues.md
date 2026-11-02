# Задача: Исправление оставшихся замечаний аудита Semrush (Duplicate content, Links with no anchor text, Pages with one internal link)

- Режим: с ревизором
- Состояние: accepted
- Рабочий каталог / ветка / исходное состояние: `D:\Workspace\clients\lily_website`, branch: main
- Выбор режима пользователем: «да подкючай и действуй» — изолированный агент task-reviewer выполнил независимую верификацию всех трёх исправлений.

## Исходное задание и уточнения

1. Запрос пользователя:
   - Запрос: Устранить оставшиеся проблемы аудита Semrush:
     1. Duplicate content (8 pages)
     2. Links with no anchor text (4 pages)
     3. Pages with only one internal link (12 pages)
   - Режим: с независимым ревизором.

## Требования и ограничения

- [x] R1 (Duplicate content, 8 страниц): Устранить дублирование страницы контактов между `/<lang>/conversations/contact/` и `/<lang>/contacts/` на всех 4 языках через 301 Permanent Redirect с `conversations:contact` на канонический маршрут `main:contacts`.
- [x] R2 (Links with no anchor text, 4 страницы): Обеспечить наличие анкорного текста или атрибута `aria-label` для всех ссылок в шапке (`_header.html`), подвале (`_footer.html`) и контенте:
  - ссылка логотипа (гарантированный `alt` и `aria-label`);
  - телефонные ссылки `tel:` (дефолтный телефон и читаемый `aria-label`);
  - ссылки на карту, мессенджеры и профили.
- [x] R3 (Pages with only one internal link, 12 страниц): Устранить дефицит внутренних ссылок на страницы сайта:
  - Добавить страницу правил бронирования (`/buchungsregeln/`) в сквозной подвал сайта (`_footer.html`) рядом с Impressum и Datenschutz на всех 4 языках (`de`, `en`, `ru`, `uk`), снабдив корректными переводами в `django.po` / `django.mo`.
  - Обеспечить кросс-линковку на страницы бронирования и юридические страницы.
- [x] R4: Проверить, что все ссылки возвращают статус 200/301, редиректы сохраняют выбранный язык, а парсер не находит ссылок с пустым анкором.

## Предположения и открытые вопросы

- Каноническим адресом страницы контактов является `/<lang>/contacts/` (приложение `features.main`).
- Маршрут `/<lang>/conversations/contact/` используется для обратной совместимости и должен постоянно (301) перенаправлять на `main:contacts`.

## План реализации

1. В `src/lily_backend/features/conversations/urls.py`:
   - Заменить прямой рендер `ContactFormView` на постоянный редирект (`RedirectView.as_view(pattern_name="main:contacts", permanent=True)`).
2. В `src/lily_backend/templates/includes/_header.html` и `_footer.html`:
   - Добавить дефолты и `aria-label` на логотип, телефон `tel:`, ссылки авторизации и внешние ссылки.
3. В `src/lily_backend/templates/includes/_footer.html`:
   - Добавить ссылку на правила бронирования `{% url 'main:buchungsregeln' %}`.
4. В файлах локализации `src/lily_backend/locale/main/*/LC_MESSAGES/django.po`:
   - Добавить ключ `nav_legal_booking_rules` (DE: "Buchungsregeln", EN: "Booking Rules", RU: "Правила бронирования", UK: "Правила бронювання") и скомпилировать `.mo`.
5. Запустить скрипт проверки ссылок и внутренних связей.
6. Запустить субагента `task-reviewer` для независимой приёмки.

## Журнал уточнений

- 2026-10-20 — Пользователь подтвердил приёмку первых двух задач и поручил подключить независимого ревизора для устранения оставшихся трёх пунктов.

## Выполнение и доказательства

| ID | Реализация pending/done | Проверка pending/pass/partial/fail/unverified и кто проверял | Доказательство и состояние результата |
| --- | --- | --- | --- |
| R1 | done | pass (ревизор: task-reviewer `pro`) | В `features/conversations/urls.py` настроен `RedirectView(pattern_name="main:contacts", permanent=True)`. Маршруты `/<lang>/conversations/contact/` на всех 4 языках отдают HTTP 301 и перенаправляют на `/<lang>/contacts/` с сохранением языка. |
| R2 | done | pass (ревизор: task-reviewer `pro`) | В `_header.html`, `_footer.html`, `impressum.html` и `contacts.html` добавлены дефолтные значения телефона, email и адреса, а также атрибуты `aria-label` для телефонных ссылок `tel:`, ссылки логотипа и ссылок на карту. Прогон по 60 страницам показал ровно 0 ссылок без анкорного текста. |
| R3 | done | pass (ревизор: task-reviewer `pro`) | Ссылка на страницу правил бронирования (`/buchungsregeln/`) добавлена в сквозной подвал `_footer.html` рядом с Impressum и Datenschutz. Добавлены переводы ключа `nav_legal_booking_rules` в `django.po` (DE, EN, RU, UK) и скомпилированы `.mo`. Каждая языковая версия `/buchungsregeln/` получила по 15 входящих внутренних ссылок. |
| R4 | done | pass (ревизор: task-reviewer `pro`) | Проверено 60 публичных URL: все отдают HTTP 200 (или 301 для устаревших маршрутов), редиректы не сбрасывают язык, битых ссылок и пустых анкоров не обнаружено. |

## Независимая ревизия

- Субагент: `task-reviewer` (модель уровня `pro`, conversation ID: `f7157dd6-a396-4e22-9ab8-cb5a26ba2412`).
- Вердикт: R1–R4: **PASS** (100% подтверждение). Все 4 существенных утверждения отчёта исполнителя признаны достоверными и подтверждены независимой проверкой.

## Разбор замечаний

Замечаний и дефектов не выявлено.

## Принятие пользователем

- 2026-10-20 — Пользователь подтвердил приёмку («принимаю тепреь дай мне отчет..»). Все замечания аудита Semrush успешно устранены и приняты.
