from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class NotificationsStates(StatesGroup):
    main = State()


STATES = NotificationsStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True


# 3. Фабрика (DI)
def create_orchestrator(container):
    from .logic.orchestrator import NotificationsOrchestrator

    # Передаем и настройки, и сам контейнер
    return NotificationsOrchestrator(settings=container.settings, container=container)
