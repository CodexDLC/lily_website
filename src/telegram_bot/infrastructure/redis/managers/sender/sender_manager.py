from codex_platform.redis_service import RedisService

from .sender_key import SenderKeys


class SenderManager:
    """
    Менеджер для управления состоянием Sender (координаты UI).
    Хранит ID сообщений (menu_msg_id, content_msg_id) в Redis.
    """

    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def get_coords(self, session_key: int | str, is_channel: bool = False) -> dict[str, int]:
        key = self._get_key(session_key, is_channel)
        data = await self.redis.hash.get_all(key)
        if not data:
            return {}
        coords = {}
        for k, v in data.items():
            try:
                coords[k] = int(v)
            except (ValueError, TypeError):
                continue
        return coords

    async def update_coords(self, session_key: int | str, coords: dict[str, int], is_channel: bool = False) -> None:
        if not coords:
            return
        key = self._get_key(session_key, is_channel)
        data_to_save = {k: str(v) for k, v in coords.items()}
        await self.redis.hash.set_fields(key, data_to_save)

    async def clear_coords(self, session_key: int | str, is_channel: bool = False) -> None:
        key = self._get_key(session_key, is_channel)
        await self.redis.string.delete(key)

    def _get_key(self, session_key: int | str, is_channel: bool) -> str:
        if is_channel:
            return SenderKeys.get_channel_coords_key(str(session_key))
        return SenderKeys.get_user_coords_key(session_key)
