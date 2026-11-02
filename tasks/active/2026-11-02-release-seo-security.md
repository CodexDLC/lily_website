# Задача: выпуск SEO-исправлений и обновлений уязвимых зависимостей

- Режим: с независимым ревизором
- Состояние: reviewed-awaiting-release
- Рабочий каталог: `D:\Workspace\clients\lily_website`
- Ветка: `main`
- Исходный production: `v2.9.7`
- Выбор режима пользователем: «да делай я не против»

## Исходный запрос

1. Закоммитить новую локальную версию, включая ранее принятые SEO-исправления.
2. Исправить зависимости, которые подтверждённо обнаруживаются security gate как уязвимые.
3. Проверить изменения и выполнить независимую ревизию.
4. Отправить коммит и новый тег в GitHub, дождаться успешной сборки образов.
5. Развернуть новую версию на production и проверить работоспособность.

## Требования и ограничения

- [ ] R1: Сопоставить незакоммиченный diff с принятыми задачами SEO/Semrush и не включать случайные или неподтверждённые изменения.
- [ ] R2: Воспроизвести dependency/security gate, подтвердить advisory и минимально обновить только необходимые зависимости и lockfile без подавления проверки.
- [ ] R3: Проверить публичные шаблоны, локализации, маршруты, canonical/hreflang, robots.txt, JSON-LD и внутренние ссылки согласно принятым SEO-задачам.
- [ ] R4: Выполнить проектный quality runner и целевые проверки; явно зафиксировать пропуски или ограничения.
- [ ] R5: Провести независимую ревизию итогового diff и устранить подтверждённые замечания до публикации.
- [ ] R6: Создать один релизный коммит и следующий свободный тег только после успешных проверок.
- [ ] R7: Дождаться успешной tag-based сборки production-образов.
- [ ] R8: Выполнить только обычный production `deploy`; не запускать `cutover_local_database`, restore или перенос данных.
- [ ] R9: После deploy проверить версии контейнеров, health endpoint, миграции и ошибки backend/system worker.

## Связанные принятые задачи

- `tasks/active/2026-10-20-fix-duplicate-title-tags.md`
- `tasks/active/2026-10-20-fix-invalid-structured-data.md`
- `tasks/active/2026-10-20-fix-semrush-remaining-audit-issues.md`

## План

1. Инвентаризировать dirty worktree и отделить release scope.
2. Воспроизвести security gate и определить минимальные исправленные версии.
3. Внести только необходимые dependency-изменения.
4. Выполнить целевые SEO/security проверки и полный quality runner.
5. Проверить итоговый diff и передать его независимому ревизору.
6. Исправить замечания, повторить проверки.
7. Создать коммит и тег, отправить в GitHub.
8. Дождаться сборки, выполнить обычный deploy и production smoke-check.

## Выполнение и доказательства

| ID | Реализация | Проверка | Доказательство |
| --- | --- | --- | --- |
| R1 | done | pass (локальная сверка + независимая ревизия) | Runtime diff сопоставлен с тремя принятыми SEO-задачами от 2026-10-20. Из release scope исключены временные `.codex-remote-attachments/`, черновик contact audit с production-контактами, непринятая задача глобального SEO-скилла и несвязанный deploy follow-up. После замечания ревизора удалён оставшийся `.codex/hooks.json`; в tracked operational-файлах Graphify больше не активируется. |
| R2 | done | pass (`check.py --security`) | Исходный lock: 161 срабатывание в 17 пакетах. Обновлены только подтверждённо уязвимые прямые зависимости и необходимые транзитивные пакеты; удалено устаревшее исключение `CVE-2026-3219`. Повторный gate: `No known vulnerabilities found`. |
| R3 | done | pass (SEO integration + gettext compile) | Расширенный rendered-page контракт: 32/32 теста, 36 публичных route/language renders и дополнительные account/service/FAQ/redirect проверки. Проверены уникальные title, canonical, de/en/ru/uk/x-default hreflang, JSON-LD, отсутствие пустых анкоров, account noindex, service detail и экранирование вредной DB-строки в FAQ. Все четыре каталога `main` локализации успешно скомпилированы. |
| R4 | done | pass (`check.py --ci` + post-review rerun) | Полный gate: quality hooks, mypy (320 source files), pip-audit, 837 unit tests с coverage 90.01%, 87 integration tests, no-cache сборка backend/worker/system_worker/nginx, healthy containers, Django system check и migration check: `ALL CI CHECKS PASSED`. После замечаний повторно прошли hooks, 837 unit tests с 90.01% и расширенные 111 integration tests. |
| R5 | done | pass (независимый ревизор) | Первоначальные замечания по FAQ JSON-LD, Graphify hooks и ширине SEO-матрицы устранены. Повторная проверка подтвердила R1/R2/R3/R5; новых существенных дефектов не выявлено. Ревизор оставил только ограничение доказательств R4, поскольку сам не повторял полный Docker gate; итоговый `check.py --ci` исполнителя завершён успешно. |
| R6 | pending | pending | |
| R7 | pending | pending | |
| R8 | pending | pending | |
| R9 | pending | pending | |

## Независимая ревизия

- Ревизор: внутренний агент `Kant` (`01a19cac-b42a-7781-bea1-017a11333adf`), read-only.
- Первоначальное заключение: R2 pass; R1/R3/R4/R5 partial; R6-R9 unverified до релизных действий.
- Существенные замечания: неэкранированный fallback `faq_a5` в JSON-LD; оставшийся Graphify hook; недостаточная свежая SEO-матрица.
- Повторная проверка исправлений: R1 pass, R2 pass, R3 pass, R5 pass; существенных находок нет.
- Ограничение ревизора: R4 partial только по независимости evidence, так как ревизор не повторял полный Docker gate. Исполнитель повторно выполнил финальный `check.py --ci` на итоговом состоянии с `ALL CI CHECKS PASSED`.

## Разбор замечаний

1. FAQ JSON-LD: значение `faq_a5` теперь выбирается в переменную и проходит `striptags|escapejs`; добавлен тест с HTML, кавычками, обратной косой чертой и переводом строки на четырёх языках.
2. Graphify cleanup: удалены tracked `.codex/hooks.json` и локальный ignored `.claude/settings.json`; полный поиск hidden/ignored-файлов показывает только безвредный ignore старого каталога `graphify-out/`.
3. SEO evidence: тест расширен до публичных маршрутов на de/en/ru/uk, account pages, service detail, hreflang, пустых анкоров, JSON-LD и legacy redirects; hostile FAQ case проходит реальную DB → manager → fake Redis → template цепочку; 32/32 теста прошли.

## Release scope

- Включить: принятые SEO/Semrush-исправления, локализации, project-skill migration, удаление устаревшего Graphify tooling, security dependency update, lockfile, CI security gate и этот task MD.
- Не включать: `.codex-remote-attachments/`, `tasks/active/2026-10-23-contact-form-audit-and-leads-recovery.md`, `tasks/active/2026-10-20-seo-architecture-skill.md`, `docs/dev/2026-10-04-deploy-ci-follow-up.md`.

## Принятие пользователем

- pending
