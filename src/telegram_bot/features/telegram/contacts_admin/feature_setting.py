from aiogram.fsm.state import State, StatesGroup


# 1. Определение состояний
class ContactsAdminStates(StatesGroup):
    main = State()  # Дашборд (Таблица) и Подменю (Список)


STATES = ContactsAdminStates

# 2. Настройки Garbage Collector
GARBAGE_COLLECT = True

# 3. Настройки Меню
MENU_CONFIG = {
    "key": "contacts_admin",
    "text": "Заявки",
    "icon": "📞",
    "description": "Управление заявками с формы сайта",
    "target_state": "contacts_admin",
    "priority": 100,
    # Права доступа
    "is_admin": True,  # Только для админов
    "is_superuser": False,
}


# 4. Фабрика (DI)
def create_orchestrator(container):
    from src.telegram_bot.core.api_client import BaseApiClient
    from src.telegram_bot.infrastructure.api_route.admin import AdminApiProvider
    from src.telegram_bot.infrastructure.redis.managers.admin.admin_cache import AdminCacheManager

    from .logic.orchestrator import ContactsAdminOrchestrator
    from .logic.provider import ContactsAdminProvider

    django_api = BaseApiClient(
        base_url=container.settings.backend_api_url, api_key=container.settings.backend_api_key, timeout=10.0
    )

    api_provider = AdminApiProvider(api_client=django_api)
    cache_manager = AdminCacheManager(redis_service=container.redis_service)

    data_provider = ContactsAdminProvider(cache=cache_manager, api=api_provider)

    return ContactsAdminOrchestrator(
        provider=data_provider, url_signer=container.url_signer, site_settings=container.site_settings
    )
