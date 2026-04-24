# Ключи для хранения данных в FSM (Redis)

# Ключ для хранения координат UI (ID сообщений Menu и Content)
KEY_UI_COORDS = "ui_coords"


class RedisStreams:
    """Redis Stream names and consumer group constants."""

    class BotEvents:
        NAME = "bot_events"
        GROUP = "bot_group"
        CONSUMER_PREFIX = "bot_instance_"
