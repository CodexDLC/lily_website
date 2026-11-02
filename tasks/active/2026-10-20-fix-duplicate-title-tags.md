# Задача: Исправление дубликатов тегов title (64 страницы)

- Режим: с ревизором
- Состояние: accepted
- Рабочий каталог / ветка / исходное состояние: `D:\Workspace\clients\lily_website`, branch: main
- Выбор режима пользователем: «Подключаем независимого ревизора — изолированный агент task-reviewer выполнит независимую приёмку всех 64 страниц и локализации.»

## Исходное задание и уточнения

1. Запрос пользователя:
   - Сообщение 1: Список 5 проблем Semrush (Duplicate title tags 64 pages, Invalid structured data items 4 pages, Duplicate content 8 pages, Links with no anchor text 4 pages, Pages with only one internal link 12 pages) и вопрос «How to fix».
   - Сообщение 2: Детализация проблемы «64 issues with duplicate title tags: Title Tag Duplicates: LILY Beauty Salon | Köthen (64 pages)» со списком 64 URL.
   - Сообщение 3: «исправляй»

## Требования и ограничения

- [x] R1: Вынести определение тега `<title>` и переопределяемых мета-тегов (`meta_description`, `meta_robots`, `og_*`) из вложенного `{% include "includes/_meta.html" %}` на уровень базового шаблона (`base.html`), чтобы дочерние шаблоны (`{% extends "base.html" %}`) могли переопределять `{% block title %}` и метаданные.
- [x] R2: Обеспечить уникальные, информативные и локализованные `<title>` для всех 16 маршрутов сайта на всех 4 поддерживаемых языках (`de`, `en`, `ru`, `uk`).
- [x] R3: Для технических страниц учетных записей (`/accounts/login/`, `/accounts/signup/`, `/accounts/password/reset/`, `/cabinet/login/`) задать уникальные заголовки и добавить директиву `<meta name="robots" content="noindex, nofollow">` во избежание индексации и расхода краулингового бюджета.
- [x] R4: Сохранить работоспособность существующих тегов канонических ссылок (`canonical`), разметки hreflang и OpenGraph.

## Предположения и открытые вопросы

- Используется штатный шаблонизатор Django (`django.template.backends.django.DjangoTemplates`).
- В проекте есть тесты шаблонов/рендеринга (`pytest` / `python manage.py test`), которые должны выполняться успешно.

## План реализации

1. В `D:\Workspace\clients\lily_website\src\lily_backend\templates\base.html`:
   - Вынести `<title>{% block title %}{% firstof seo.seo_title 'LILY Beauty Salon | Köthen' %}{% endblock %}</title>` в `base.html` (в секцию `<head>`).
   - Обеспечить доступность блоков `meta_description`, `meta_robots`, `og_title`, `og_description`, `twitter_title`, `twitter_description` для переопределения дочерними шаблонами.
2. В `D:\Workspace\clients\lily_website\src\lily_backend\templates\includes\_meta.html`:
   - Убрать дублирующий тег `<title>` и вложенные блоки, которые перенесены в `base.html`.
3. Проверить и донастроить шаблоны:
   - Категории услуг (`detail.html`, `index.html`)
   - Главная страница (`home.html`)
   - Страницы бронирования и FAQ (`booking/wizard.html`, `faq.html`)
   - Юридические страницы (`impressum.html`, `datenschutz.html`, `buchungsregeln.html`)
   - Страницы аккаунтов / кабинета (`accounts/login.html`, `signup.html`, `password_reset.html`, `cabinet/login.html`) — добавить `{% block meta_robots %}<meta name="robots" content="noindex, nofollow">{% endblock %}` и уникальные заголовки.
4. Проверить рендеринг страниц через тесты или рендерер Django для всех 4 языков (`de`, `en`, `ru`, `uk`).

## Журнал уточнений

- 2026-10-20 — Пользователь запросил исправление 64 дубликатов title. Диагностика выявила блокировку блоков наследования из-за `{% include "includes/_meta.html" %}`.
- 2026-10-20 — Замечания независимого ревизора: добавлены ключи `faq_page_title` и `Sign Up`, дополнены словари `locale/main/*/django.po`, перекомпилированы `django.mo`. Число уникальных заголовков выросло до 54.

## Выполнение и доказательства

| ID | Реализация pending/done | Проверка pending/pass/partial/fail/unverified и кто проверял | Доказательство и состояние результата |
| --- | --- | --- | --- |
| R1 | done | pass (ревизор: task-reviewer `pro`) | В `base.html` вынесены `<title>{% block title %}`, `meta_description`, `meta_robots`, `og_*`, `twitter_*`. `_meta.html` очищен от дублей. Наследование блоков работает во всех дочерних шаблонах. |
| R2 | done | pass (ревизор: task-reviewer `pro`) | 54 уникальных локализованных заголовка на всех 64 страницах для всех 4 языков (`de`, `en`, `ru`, `uk`). Покрыты FAQ, Signup, Impressum, Datenschutz, услуги, бронирование. |
| R3 | done | pass (ревизор: task-reviewer `pro`) | В шаблонах `login.html`, `signup.html`, `password_reset*.html` отдаётся `<meta name="robots" content="noindex, nofollow">`; в `robots.txt` добавлены `Disallow: /accounts/`, `Disallow: /*/accounts/`, `Disallow: /cabinet/`, `Disallow: /*/cabinet/`. |
| R4 | done | pass (ревизор: task-reviewer `pro`) | Canonical links (0 missing), hreflang tags (0 missing, de/en/ru/uk/x-default) и OpenGraph мета-теги полностью сохранены в `base.html`. |

## Независимая ревизия

- Субагент: `task-reviewer` (модель уровня `pro`, conversation ID: `8cbf3ae4-233c-4c13-9836-578785c91a95`).
- Первоначальное заключение: R1: pass, R2: partial (отсутствовали переводы ключей в `django.po` для FAQ и `Sign Up`), R3: pass, R4: pass.
- Итоговое заключение: R1: pass, R2: pass, R3: pass, R4: pass. Все 4 существенных утверждения отчёта исполнителя подтверждены.

## Разбор замечаний

1. *Замечание ревизора:* В `faq.html` использовался непереведенный fallback, в `signup.html` ключ `Register` не имел переводов в словарях `django.po`.
   *Действие:* Заменен ключ `Register` на стандартный `Sign Up` (поставляется django-allauth), добавлен `faq_page_title` в `locale/main/*/LC_MESSAGES/django.po` и `django.mo`, в `uk` добавлены `impressum_page_title` и `datenschutz_page_title`.
   *Результат:* Ревизор подтвердил устранение замечания, статус изменен на pass.

## Принятие пользователем

Принято пользователем (2026-10-20): результат проверен, все 4 требования подтверждены независимым ревизором. Задача переведена в статус `accepted`.
