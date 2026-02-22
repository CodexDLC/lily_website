from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clears the entire Django cache (Redis)"

    def handle(self, *args, **options):
        self.stdout.write("Clearing Django cache...")
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Successfully cleared cache."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to clear cache: {e}"))
