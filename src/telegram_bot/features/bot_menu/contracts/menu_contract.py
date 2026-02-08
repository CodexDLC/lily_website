from typing import Protocol


class MenuDiscoveryProvider(Protocol):
    """
    Контракт для получения списка кнопок меню.
    Реализуется сервисом FeatureDiscoveryService.
    """
    def get_menu_buttons(self) -> dict[str, dict]: ...
