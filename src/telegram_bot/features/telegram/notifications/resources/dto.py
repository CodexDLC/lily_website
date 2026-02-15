from pydantic import BaseModel, Field


class QueryContext(BaseModel):
    """
    Pydantic-модель для хранения извлеченной информации из CallbackQuery.
    """

    user_id: int = Field(..., description="ID пользователя, инициировавшего callback")
    chat_id: int | None = Field(None, description="ID чата, в котором произошло событие")
    message_thread_id: int | None = Field(None, description="ID топика (форума), если сообщение было в топике")
    action: str = Field(..., description="Действие из callback_data")
    session_id: int | str | None = Field(None, description="ID сессии, может быть числом или строкой")
    message_text: str | None = Field(None, description="Текст сообщения, к которому относится callback")
    message_id: int | None = Field(
        None, description="ID сообщения, к которому относится callback"
    )  # Добавлено message_id
