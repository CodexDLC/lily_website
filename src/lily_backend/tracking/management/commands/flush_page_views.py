from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Flush today's page view counters from Redis into the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=None,
            help="Date to flush in YYYY-MM-DD format (default: today)",
        )

    def handle(self, *args, **options):
        from tracking.flush import flush_page_views

        date_str = options["date"] or timezone.now().strftime("%Y-%m-%d")
        count = flush_page_views(date_str)
        self.stdout.write(self.style.SUCCESS(f"[tracking] flushed {count} paths for {date_str}"))
