from codex_django.system.management.base_commands import BaseUpdateAllContentCommand


class Command(BaseUpdateAllContentCommand):
    """
    Run all content update commands and clear cache.
    Useful to run during entrypoint initialization or deployments.
    """

    help = "Run all content update commands and clear cache"

    commands_to_run = [
        "update_site_settings",
        "update_static_translations",
        "update_email_content",
        "update_seo",
    ]

    _labels = {
        "update_site_settings": "Updating Site Settings",
        "update_static_translations": "Updating Static Translations",
        "update_email_content": "Updating Email Content",
        "update_seo": "Updating Static Page SEO",
    }

    def get_command_label(self, command_name: str) -> str:
        return self._labels.get(command_name, command_name)

    def before_subcommand(self, command_name: str) -> None:
        self.stdout.write(f"\n--- {self.get_command_label(command_name)} ---")
