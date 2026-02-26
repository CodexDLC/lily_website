from core.logger import log
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all content update commands and clear cache"

    def handle(self, *args, **options):
        log.info("Command: update_all_content | Action: Start")

        try:
            log.debug("Command: update_all_content | Action: SubCommand | name=update_site_settings")
            call_command("update_site_settings")

            log.debug("Command: update_all_content | Action: SubCommand | name=update_static_translations")
            call_command("update_static_translations")

            log.debug("Command: update_all_content | Action: SubCommand | name=update_services_seo")
            call_command("update_services_seo")

            log.debug("Command: update_all_content | Action: SubCommand | name=update_static_seo")
            call_command("update_static_seo")

            log.debug("Command: update_all_content | Action: SubCommand | name=load_main_data")
            call_command("load_main_data")

            log.debug("Command: update_all_content | Action: SubCommand | name=load_services")
            call_command("load_services")

            log.debug("Command: update_all_content | Action: SubCommand | name=update_masters")
            call_command("update_masters")

            log.info("Command: update_all_content | Action: Success")
            self.stdout.write(self.style.SUCCESS("\nAll updates completed. Cache invalidated selectively per change."))

        except Exception as e:
            log.error(f"Command: update_all_content | Action: Failed | error={e}")
            self.stdout.write(self.style.ERROR(f"Update failed: {e}"))
            raise
