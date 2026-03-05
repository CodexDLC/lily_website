from codex_tools.notifications.adapters.django_adapter import DjangoNotificationAdapter
from codex_tools.notifications.selector import BaseEmailContentSelector
from core.arq.client import DjangoArqClient

from ..models.email_content import EmailContent


class EmailContentSelector(BaseEmailContentSelector):
    """
    Project-specific selector using Django adapter.
    """

    def __init__(self):
        # Pass the enqueue function to the adapter
        adapter = DjangoNotificationAdapter(enqueue_func=DjangoArqClient.enqueue_job)
        super().__init__(model_class=EmailContent, adapter=adapter)


# Singleton instance
selector = EmailContentSelector()
