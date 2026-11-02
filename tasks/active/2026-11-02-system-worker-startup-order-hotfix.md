# Задача: устранить гонку запуска system worker

- Режим: с независимым ревизором
- Состояние: reviewed-awaiting-release
- Рабочий каталог: `D:\Workspace\clients\lily_website`
- Базовый production: `v2.9.8`

## Причина

После штатного deploy `v2.9.8` контейнер `system_worker` стартовал одновременно с
`backend`. Его startup-задачи попытались обратиться к
`http://backend:8000` до готовности API и завершились с `ConnectError`.

## Требования

- [x] H1: production `system_worker` должен запускаться только после
  healthy-состояния `backend`, `db` и `redis`; существующий контракт test/dev
  должен остаться без изменений.
- [x] H2: Итоговые compose-конфигурации должны успешно проходить
  `docker compose config`.
- [x] H3: Изменение должно пройти независимую ревизию.
- [ ] H4: Выпустить исправляющий тег и выполнить обычный production `deploy` без
  cutover, restore или переноса данных.
- [ ] H5: После deploy подтвердить отсутствие startup-ошибок, healthy backend,
  актуальные образы, миграции и внешний HTTPS.

## План

1. Добавить зависимость `backend: condition: service_healthy` для production
   `system_worker`; подтвердить, что test/dev уже имеют такой контракт.
2. Проверить нормализованные compose-конфигурации и итоговый diff.
3. Выполнить независимую ревизию.
4. Создать hotfix-коммит и тег, собрать образы и выполнить обычный deploy.
5. Проверить фактическое состояние VPS и свежие логи.

## Доказательства

| ID | Состояние | Доказательство |
| --- | --- | --- |
| H1 | pass | Production `system_worker` ожидает healthy `backend`, `db` и `redis`; test/dev уже имели такой порядок и не изменены. |
| H2 | pass | `docker compose config --no-env-resolution --quiet` завершён успешно; нормализованный `depends_on` содержит три `service_healthy`. |
| H3 | pass | Независимый ревизор подтвердил отсутствие цикла (`system_worker -> backend -> db/redis`), корректный healthcheck и применение зависимости штатным deploy workflow. |
| H4 | pending | |
| H5 | pending | |

## Независимая ревизия

- Ревизор: внутренний агент `Kant` (`01a19cac-b42a-7781-bea1-017a11333adf`), read-only.
- Вердикт: `PASS`, блокирующих и существенных замечаний нет.
- Остаточное ограничение: `depends_on` регулирует первоначальный порядок запуска, но
  не отслеживает последующую потерю health и автономные Docker-restarts; это не
  относится к обнаруженной startup-гонке.
