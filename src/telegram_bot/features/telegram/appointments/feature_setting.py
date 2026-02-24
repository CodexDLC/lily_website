from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class AppointmentsStates(StatesGroup):
    main = State()  # Все экраны фичи (Hub / Dashboard / Category)


STATES = AppointmentsStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True

# 3. Настройки Меню (priority=40 — выше чем contacts_admin=100, уступает notifications=50)
MENU_CONFIG = {
    "key": "appointments",
    "text": "Записи",
    "icon": "📋",
    "description": "Управление записями клиентов",
    "target_state": "appointments",
    "priority": 40,
    "is_admin": True,
    "is_superuser": False,
}


# 4. Фабрика (DI)
def create_orchestrator(container):
    from src.telegram_bot.core.api_client import BaseApiClient
    from src.telegram_bot.infrastructure.api_route.appointments import AppointmentsApiProvider

    from .logic.orchestrator import AppointmentsOrchestrator
    from .logic.provider import AppointmentsProvider

    django_api = BaseApiClient(
        base_url=container.settings.backend_api_url,
        api_key=container.settings.backend_api_key,
        timeout=10.0,
    )

    api_provider = AppointmentsApiProvider(api_client=django_api)
    data_provider = AppointmentsProvider(api=api_provider)

    return AppointmentsOrchestrator(
        provider=data_provider,
        url_signer=container.url_signer,
        site_settings=container.site_settings,
    )
