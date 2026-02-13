from typing import cast

from django.db.models import Q
from django.utils import timezone

from ..models import Client


class ClientService:
    """Service for managing Client logic, refactored for clarity."""

    @staticmethod
    def get_or_create_client(
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
        email: str = "",
        instagram: str = "",
        telegram: str = "",
        consent_marketing: bool = False,
    ) -> Client:
        """
        Finds a client by phone or email, or creates/updates one.
        Orchestrates finding, creating, and updating logic.
        """
        normalized_phone = ClientService._normalize_phone(phone)

        client = ClientService._find_client(phone=normalized_phone, email=email)

        client_data = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": normalized_phone,
            "email": email,
            "instagram": instagram,
            "telegram": telegram,
            "consent_marketing": consent_marketing,
        }

        if not client:
            return ClientService._create_new_client(client_data)

        return ClientService._update_existing_client(client, client_data)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Strips whitespace and hyphens from a phone number."""
        if not phone:
            return ""
        return phone.strip().replace(" ", "").replace("-", "")

    @staticmethod
    def _find_client(phone: str, email: str) -> Client | None:
        """
        Finds a client using a prioritized, two-step search:
        1. Tries to find an exact match on both phone AND email.
        2. If not found, tries to find a match on phone OR email.
        """
        if not phone and not email:
            return None

        # 1. Exact match (AND)
        if phone and email:
            client = cast("Client | None", Client.objects.filter(phone=phone, email=email).first())
            if client:
                return client

        # 2. Partial match (OR)
        query = Q()
        if phone:
            query |= Q(phone=phone)
        if email:
            query |= Q(email=email)

        if not query:
            return None

        # Return the first match found. This is a performance trade-off.
        # The database's default ordering will determine which client is returned
        # if multiple clients match the OR condition.
        return cast("Client | None", Client.objects.filter(query).first())

    @staticmethod
    def _create_new_client(data: dict) -> Client:
        """Creates a new client record."""
        return cast(
            "Client",
            Client.objects.create(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                instagram=data.get("instagram", ""),
                telegram=data.get("telegram", ""),
                status=Client.STATUS_GUEST,
                consent_marketing=data.get("consent_marketing", False),
                consent_date=timezone.now() if data.get("consent_marketing") else None,
            ),
        )

    @staticmethod
    def _update_existing_client(client: Client, data: dict) -> Client:
        """Updates an existing client with new data if fields are empty."""
        update_fields = []

        fields_to_update = {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "instagram": data.get("instagram"),
            "telegram": data.get("telegram"),
        }

        for field, value in fields_to_update.items():
            if value and not getattr(client, field):
                setattr(client, field, value)
                update_fields.append(field)

        if data.get("consent_marketing") and not client.consent_marketing:
            client.consent_marketing = True
            client.consent_date = timezone.now()
            update_fields.extend(["consent_marketing", "consent_date"])

        if update_fields:
            client.save(update_fields=update_fields)

        return client
