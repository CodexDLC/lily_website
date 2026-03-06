# 📦 Booking DTOs (Data Transfer Objects)

[⬅️ Назад](./README.md) | [🏠 Корень Документации](../../README.md)

Объекты передачи данных (Data Transfer Objects) — это основной интерфейс для работы с движком бронирования.
Все DTO объявлены в `codex_tools.booking.dto`. Они используют Pydantic `v2` и строго иммутабельны (`frozen=True`), чтобы предотвратить побочные эффекты во время работы алгоритмов перебора (backtracking).

## Входные DTO (Input DTOs)

### `ServiceRequest`
Представляет одну услугу, запрошенную клиентом.

- `service_id (str)`: Уникальный ID услуги.
- `duration_minutes (int)`: Основная длительность.
- `gap_after_minutes (int)`: Время, которое блокируется после услуги (для уборки кабинета, подготовки к следующему клиенту).
- `allowed_master_ids (list[str])`: Список мастеров, способных выполнить эту услугу.

### `BookingEngineRequest`
Полный запрос (payload), который передается в `ChainFinder.find()`.

- `service_requests (list[ServiceRequest])`: Последовательность желаемых услуг.
- `target_date (date)`: Желаемая дата.
- `mode (BookingMode)`: Может быть `SINGLE_DAY` (один день) или `MULTIPLE_DAYS` (несколько дней).

## DTO Доступности (Availability DTOs)

### `MasterAvailability`
Предоставляется Адаптером до запуска движка. Используется движком, чтобы знать, какое время свободно.

- `master_id (str)`
- `free_windows (list[tuple[datetime, datetime]])`: Например, `[(09:00, 13:00), (14:00, 18:00)]`.
- `buffer_between_minutes (int)`: Общий буфер мастера (пауза), который требуется между разными клиентами.

## Выходные DTO (Output DTOs)

### `BookingChainSolution`
Один валидный вариант расписания записей, найденный движком.

- `services (list[SingleServiceSolution])`: Конкретные выделенные слоты.
- `span_minutes()`: Общее время, занимаемое цепочкой от старта первой услуги до конца последней.

### `EngineResult`
Окончательный возвращаемый объект из `ChainFinder`.

- `chains (list[BookingChainSolution])`: Содержит все возможные решения.
- `errors (list[str])`: Если пусто, значит слоты найдены (или их вообще нет в расписании). Если заполнено, значит что-то не так с самим запросом (например, конфликтующие требования к мастерам).
