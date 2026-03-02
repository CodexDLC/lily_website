import httpx
from loguru import logger as log


class SevenIOClient:
    """
    Client for Seven.io API (SMS and WhatsApp).
    """

    def __init__(self, api_key: str, from_name: str = "LILY"):
        self.api_key = api_key
        self.from_name = from_name
        self.base_url = "https://gateway.seven.io/api"

    async def send_sms(self, to_number: str, text: str) -> bool:
        """
        Sends SMS via Seven.io.
        """
        params: dict[str, str | int] = {
            "p": str(self.api_key),
            "to": str(to_number),
            "text": str(text),
            "from": str(self.from_name),
            "json": 1,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/sms", params=params)
                response.raise_for_status()
                data = response.json()

                # Check status code in JSON response
                if (
                    data.get("success") == "100"
                    or data.get("success") is True
                    or any(m.get("success") for m in data.get("messages", []))
                ):
                    log.info(f"SevenIOClient | SMS sent to {to_number}")
                    return True
                else:
                    log.error(f"SevenIOClient | SMS failed: {data}")
                    return False
        except Exception as e:
            log.error(f"SevenIOClient | SMS error: {e}")
            return False

    async def send_whatsapp(self, to_number: str, text: str) -> bool:
        """
        Sends WhatsApp message via Seven.io.
        """
        # Note: Seven.io WhatsApp might require a specific endpoint or parameters
        # Based on docs, it's often handled via the 'whatsapp' endpoint
        payload = {
            "to": to_number,
            "text": text,
            "from": self.from_name,
        }
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/whatsapp", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                if data.get("success") or data.get("status") == "success":
                    log.info(f"SevenIOClient | WhatsApp sent to {to_number}")
                    return True
                else:
                    log.error(f"SevenIOClient | WhatsApp failed: {data}")
                    return False
        except Exception as e:
            log.error(f"SevenIOClient | WhatsApp error: {e}")
            return False
