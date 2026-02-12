from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class DjangoListenerStates(StatesGroup):
    main = State()


STATES = DjangoListenerStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True

# 3. Настройки Меню (Закомментировано, так как фича не интерактивна)
# MENU_CONFIG = {
#     "key": "django_listener",
#     "text": "✨ DjangoListener",
#     "icon": "✨",
#     "description": "Описание фичи DjangoListener",
#     "target_state": "django_listener",
#     "priority": 50,
#     # Права доступа
#     "is_admin": False,      # Только для владельцев (Owner)
#     "is_superuser": False,  # Только для разработчиков (Superuser)
# }


# 4. Фабрика (DI)
def create_orchestrator(container):
    from .logic.orchestrator import DjangoListenerOrchestrator

    # Больше не передаем stream_processor, так как оркестратор его не принимает
    return DjangoListenerOrchestrator()
