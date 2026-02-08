from aiogram.filters.callback_data import CallbackData

class {class_name}Callback(CallbackData, prefix="{feature_key}"):
    """
    CallbackData для фичи {class_name}.
    action: действие (main, detail, etc.)
    id: опциональный идентификатор
    """
    action: str
    id: int | None = None
