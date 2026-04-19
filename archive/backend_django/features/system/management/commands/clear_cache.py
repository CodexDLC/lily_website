from core.logger import log
from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clears the entire Django cache (Redis)"

    def handle(self, *args, **options):
        log.info("Command: clear_cache | Action: Start")
        try:
            cache.clear()
            log.info("Command: clear_cache | Action: Success | status=CacheCleared")
            self.stdout.write(self.style.SUCCESS("Successfully cleared cache."))
        except Exception as e:
            log.error(f"Command: clear_cache | Action: Failed | error={e}")
            self.stdout.write(self.style.ERROR(f"Failed to clear cache: {e}"))
            raise
