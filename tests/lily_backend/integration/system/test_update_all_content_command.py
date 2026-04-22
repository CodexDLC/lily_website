from unittest.mock import patch

from django.core.management import call_command


def test_update_all_content_uses_base_command_hooks():
    with patch("codex_django.system.management.base_commands.call_command") as mocked_call_command:
        call_command("update_all_content", force=True)

        assert [call.args[0] for call in mocked_call_command.call_args_list] == [
            "update_site_settings",
            "update_static_translations",
            "update_email_content",
            "update_seo",
        ]
        for call in mocked_call_command.call_args_list:
            assert call.kwargs["force"] is True
