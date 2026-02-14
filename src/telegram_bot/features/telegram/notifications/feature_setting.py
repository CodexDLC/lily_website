from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class NotificationsStates(StatesGroup):
    main = State()


STATES = NotificationsStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True

# 3. Настройки Меню
MENU_CONFIG = {
    "key": "notifications",
    "text": "✨ Notifications",
    "icon": "✨",
    "description": "Описание фичи Notifications",
    "target_state": "notifications",
    "priority": 50,
    # Права доступа
    "is_admin": False,  # Только для владельцев (Owner)
    "is_superuser": False,  # Только для разработчиков (Superuser)
}


# 4. Фабрика (DI)
def create_orchestrator(container):
    from .logic.orchestrator import NotificationsOrchestrator

    # Временная заглушка для провайдера данных
    # В будущем здесь будет реальный репозиторий или API клиент
    data_provider = None

    return NotificationsOrchestrator(data_provider=data_provider)
