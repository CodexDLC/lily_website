import hashlib
import hmac
from urllib.parse import unquote

from django.conf import settings


def validate_hmac_signature(request_id: str, timestamp: str, signature: str) -> bool:
    """
    Validates the HMAC-SHA256 signature for a given request_id and timestamp.
    """
    if not request_id or not timestamp or not signature:
        return False

    secret_key = settings.SECRET_KEY.encode("utf-8")
    payload = f"{request_id}:{timestamp}".encode()

    expected_signature = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def validate_telegram_init_data(init_data: str, bot_token: str | None = None) -> bool:
    """
    Validates the Telegram WebApp initData payload.
    """
    if not init_data:
        return False

    if bot_token is None:
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        # If no bot token configured, we might want to fail securely
        # or log a warning depending on environment.
        return False

    try:
        # Parse initData
        parsed_data = dict(qc.split("=") for qc in unquote(init_data).split("&"))

        if "hash" not in parsed_data:
            return False

        received_hash = parsed_data.pop("hash")

        # Sort data alphabetically by keys
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        # Cryptography
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        return hmac.compare_digest(calculated_hash, received_hash)
    except Exception:
        return False
