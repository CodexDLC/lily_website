from pydantic import BaseModel


class NotificationsPayload(BaseModel):
    """
    DTO для передачи данных внутри фичи Notifications.
    """

    id: int
    # Добавьте свои поля здесь
