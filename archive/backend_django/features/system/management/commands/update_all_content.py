from core.logger import log
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run all content update commands and clear cache"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Ignore hash checks and force all updates")

    def handle(self, *args, **options):
        log.info("Command: update_all_content | Action: Start")
        force = options.get("force", False)
        errors = []

        commands = [
            "update_static_translations",
            "update_email_content",
            "update_static_seo",
            "load_main_data",
            "load_services",
            "update_masters",
        ]

        for cmd in commands:
            try:
                log.debug(f"Command: update_all_content | Action: SubCommand | name={cmd}")
                call_command(cmd, force=force)
            except Exception as e:
                msg = f"Subcommand {cmd} failed: {e}"
                log.error(f"Command: update_all_content | Action: SubError | error={msg}")
                errors.append(msg)

        if errors:
            self.stdout.write(self.style.ERROR(f"Update completed with {len(errors)} errors."))
            for err in errors:
                self.stdout.write(self.style.ERROR(f" - {err}"))
            raise CommandError("One or more subcommands failed.")

        log.info("Command: update_all_content | Action: Success")
        self.stdout.write(self.style.SUCCESS("\nAll updates completed. Cache invalidated selectively per change."))
