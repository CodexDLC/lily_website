from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class NotificationsStates(StatesGroup):
    main = State()


STATES = NotificationsStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True


# 3. Фабрика (DI)
def create_orchestrator(container):
    from src.telegram_bot.core.api_client import BaseApiClient
    from src.telegram_bot.infrastructure.api_route.appointments import AppointmentsApiProvider

    from .logic.orchestrator import NotificationsOrchestrator

    # Настраиваем API провайдер
    django_api = BaseApiClient(
        base_url=container.settings.backend_api_url, api_key=container.settings.backend_api_key, timeout=10.0
    )
    appointments_provider = AppointmentsApiProvider(api_client=django_api)

    # Передаем и настройки, и сам контейнер, и зависимости
    return NotificationsOrchestrator(
        settings=container.settings, container=container, appointments_provider=appointments_provider
    )
