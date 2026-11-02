from pathlib import Path

from codex_core.dev.check_runner import BaseCheckRunner

from tools.dev.check import LilyCheckRunner


def test_windows_tool_command_uses_python_module(monkeypatch, tmp_path: Path) -> None:
    python = tmp_path / ".venv" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.touch()
    runner = LilyCheckRunner(tmp_path)
    captured: dict[str, object] = {}

    def capture_command(
        _runner: BaseCheckRunner,
        command: object,
        *,
        capture_output: bool = True,
        env: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        captured["command"] = command
        captured["capture_output"] = capture_output
        captured["env"] = env
        return True, ""

    monkeypatch.setattr(BaseCheckRunner, "run_command", capture_command)

    success, _ = runner.run_command("pre-commit run --all-files")

    assert success is True
    assert captured["command"] == f'"{python}" -m pre_commit run --all-files'
