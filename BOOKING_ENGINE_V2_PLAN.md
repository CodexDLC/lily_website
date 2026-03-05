# План разработки: Универсальный движок бронирования (Booking Engine V2)

Этот документ содержит пошаговую инструкцию и архитектурный чертеж для реализации новой системы бронирования.

---

## 1. ЦЕЛЬ
Создать изолированный "движок" (Engine) для бизнес-логики бронирования, который:
1.  **Универсален:** Не зависит от Django и может быть вынесен в отдельную библиотеку.
2.  **Гибок:** Поддерживает поиск слотов с мелким шагом (30 мин) и сложные цепочки услуг (Combo).
3.  **Чист:** Оперирует простыми типами данных (DTO), а не моделями базы данных.

---

## 2. АРХИТЕКТУРА (Engine/Adapter Pattern)

### 2.1. Движок (`features/booking/engine/`)
*   **Ответственность:** Чистая математика бронирования.
*   **Запрет:** Никаких импортов из Django (`models`, `views`, `timezone` и т.д.).
*   **Данные:** Использует `dataclasses` (DTO) для входных и выходных данных.

### 2.2. Адаптер (`features/booking/services/`)
*   **Ответственность:** Мост между Django и Движком.
*   **Процесс:**
    1. Получает данные из моделей (`Master`, `Service`, `Appointment`).
    2. Конвертирует их в DTO.
    3. Вызывает Движок.
    4. Преобразует результат Движка в формат, нужный для `View` (например, `["08:00", "08:30"]`).

---

## 3. ПОШАГОВЫЙ ПЛАН РЕАЛИЗАЦИИ

### ФАЗА 1: Подготовка структуры
1. Создать папку `src/backend_django/features/booking/engine/`.
2. Создать файлы `dto.py` и `chain_finder.py` внутри этой папки.
3. Создать документацию в `docs/en_EN/architecture/backend_django/features/booking/README.md`.

### ФАЗА 2: Реализация Движка (Core)
1. **В `dto.py`** описать структуры: `ServiceRequest`, `BookingRequest`, `TimeSlot`, `BookingSolution`.
2. **В `chain_finder.py`** реализовать:
    *   `_find_slots_in_window`: Алгоритм "скользящего окна" (шаг 30 мин).
    *   `find_booking_chains`: Главная функция поиска (сначала для 1 услуги, затем расширить для цепочек).

### ФАЗА 3: Интеграция (Adapter)
1. Рефакторинг `features/booking/services/slots.py`.
2. Метод `get_available_slots` должен стать "переводчиком": собирать данные из БД -> вызывать движок -> отдавать результат во View.

---

## 4. АРХИТЕКТУРНЫЙ ЧЕРТЕЖ (Код)

```python
# --- DTO (engine/dto.py) ---
@dataclass(frozen=True)
class ServiceRequest:
    service_id: str
    duration_minutes: int
    possible_master_ids: List[str]

@dataclass(frozen=True)
class BookingRequest:
    service_requests: List[ServiceRequest]
    booking_date: date

# --- ENGINE (engine/chain_finder.py) ---
def find_booking_chains(request, masters_availability, step_minutes=30):
    # Логика поиска цепочек здесь.
    # masters_availability - это Dict[master_id, List[Tuple[start, end]]]
    pass

# --- ADAPTER (services/slots.py) ---
class SlotService:
    def get_available_slots(self, masters, service, date_obj, step_minutes=30):
        # 1. Модели -> DTO
        # 2. find_booking_chains(...)
        # 3. Результат -> ["08:00", ...]
        pass
```

---

## 5. ПРИЕМКА (Definition of Done)
- [ ] Код в `engine/` не содержит импортов из `django`.
- [ ] В Кабинете при создании записи слоты отображаются с шагом 30 минут.
- [ ] Система готова к добавлению второй услуги в запрос без переписывания ядра.
