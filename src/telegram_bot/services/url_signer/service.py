import hashlib
import hmac
import time
from urllib.parse import quote_plus, urlencode

from src.telegram_bot.core.config import BotSettings


class UrlSignerService:
    """
    Service for generating HMAC-signed URLs for Telegram Mini Apps.
    This ensures that URLs are tamper-proof and have a limited lifespan.
    """

    def __init__(self, settings: BotSettings):
        self.secret_key = settings.secret_key.encode("utf-8")

    def generate_signed_url(self, base_url: str, request_id: str | int, action: str = "reply") -> str:
        """
        Generates a full signed URL for the WebApp.

        Args:
            base_url: The root URL of the site (e.g., https://lily-salon.de)
            request_id: The ID of the request handling the reply
            action: The action path (default is reply)

        Returns:
            URL string with appended HMAC signature
        """
        timestamp = str(int(time.time()))
        req_id_str = str(request_id)

        # Base string to sign: "request_id:timestamp"
        payload = f"{req_id_str}:{timestamp}".encode()

        # Calculate HMAC-SHA256 signature
        signature = hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()

        # Build query parameters
        params = {"req_id": req_id_str, "ts": timestamp, "sig": signature}

        # Strip trailing slashes and ensure clean path
        clean_base_url = base_url.rstrip("/")

        # Construct the final URL
        return f"{clean_base_url}/tma/{action}/?{urlencode(params, quote_via=quote_plus)}"
