import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from codex_core.dev.check_runner import BaseCheckRunner, Colors

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "deploy" / "docker-compose.test.yml"
TEST_PROJECT_NAME = "lily-quality-check"


class LilyCheckRunner(BaseCheckRunner):
    """Quality gate runner that preserves legacy Docker validation logic."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        # We enforce venv via run_command override to be more precise

    def run_command(
        self,
        command: str | Sequence[str],
        *,
        capture_output: bool = True,
        env: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        """Wrap commands to use .venv binaries if available."""
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        venv_scripts = self.project_root / ".venv" / "Scripts"

        # Create a copy/ref to avoid mutating the original Sequence if it's a list
        cmd = list(command) if isinstance(command, (list, tuple)) else command

        if venv_python.exists():
            # Handle both string and list commands
            if isinstance(cmd, str):
                parts = cmd.split()
                if parts:
                    main_tool = parts[0].replace(".exe", "").lower()
                    # If calling python directly, swap to venv python
                    if "python" in main_tool:
                        cmd = cmd.replace(parts[0], f'"{venv_python}"', 1)
                    # If calling a tool, use the venv binary if it exists
                    elif main_tool in ["pytest", "ruff", "mypy", "pip-audit", "pre-commit"]:
                        binary = venv_scripts / f"{main_tool}.exe"
                        if binary.exists():
                            cmd = cmd.replace(parts[0], f'"{binary}"', 1)

            elif isinstance(cmd, list) and cmd:
                main_tool = str(cmd[0]).replace(".exe", "").lower()
                # If calling python directly, swap to venv python
                if "python" in main_tool:
                    cmd[0] = str(venv_python)
                # If calling a tool, use the venv binary if it exists
                elif main_tool in ["pytest", "ruff", "mypy", "pip-audit", "pre-commit"]:
                    binary = venv_scripts / f"{main_tool}.exe"
                    if binary.exists():
                        cmd[0] = str(binary)

        return super().run_command(cmd, capture_output=capture_output, env=env)

    def docker_compose(self, args: str, capture_output: bool = True) -> tuple[bool, str]:
        env = os.environ.copy()
        env["CONTAINER_PREFIX"] = TEST_PROJECT_NAME
        cmd = f"docker compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} {args}"
        return self.run_command(cmd, env=env, capture_output=capture_output)

    def print_docker_logs(self) -> None:
        print(f"\n{Colors.BLUE}📋 Fetching container logs for debugging...{Colors.ENDC}")
        self.docker_compose("logs --tail=100", capture_output=False)

    def wait_for_services_healthy(self, timeout: int = 120) -> bool:
        self.print_step(f"Waiting for services to be ready (timeout: {timeout}s)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            # Simple progress bar
            bar_width = 30
            filled = min(bar_width, int(bar_width * elapsed / timeout))
            bar = "#" * filled + "." * (bar_width - filled)
            sys.stdout.write(f"\r[{bar}] {elapsed}/{timeout}s Checking status... ")
            sys.stdout.flush()

            success, output = self.docker_compose("ps --format json")
            if not success or not output:
                time.sleep(3)
                continue

            try:
                # Docker Compose can return multiple JSON objects or a list
                lines = [L for L in output.strip().split("\n") if L.strip()]
                containers = []
                for line in lines:
                    try:
                        data = json.loads(line)
                        if isinstance(data, list):
                            containers.extend(data)
                        else:
                            containers.append(data)
                    except json.JSONDecodeError:
                        continue

                if not containers:
                    time.sleep(3)
                    continue

                all_ready = True
                for container in containers:
                    name = container.get("Name", "Unknown")
                    status = str(container.get("Status", container.get("State", ""))).lower()
                    health = str(container.get("Health", "")).lower()

                    if "unhealthy" in health:
                        print(f"\n{Colors.BLUE}❌ Container {name} is unhealthy!{Colors.ENDC}")
                        return False

                    if "exited" in status or "dead" in status:
                        print(f"\n{Colors.BLUE}❌ Container {name} has stopped unexpectedly!{Colors.ENDC}")
                        return False

                    # If has health state reported, wait for healthy. If not, wait for running/up/started.
                    if health and health not in ["none", "null", "undefined"]:
                        if "healthy" not in health:
                            all_ready = False
                            break
                    else:
                        # Fallback to status check
                        if not any(s in status for s in ["running", "up", "started"]):
                            all_ready = False
                            break

                if all_ready:
                    print(f"\n{Colors.GREEN}✅ All services are ready!{Colors.ENDC}")
                    return True
            except Exception:
                pass

            time.sleep(3)

        print(f"\n{Colors.BLUE}❌ Timeout waiting for services to be healthy.{Colors.ENDC}")
        return False

    def cleanup_docker(self) -> None:
        print(f"\n{Colors.BLUE}🧹 Cleaning up Docker resources (Project: {TEST_PROJECT_NAME})...{Colors.ENDC}")
        # --rmi all removes all images built by this project
        self.docker_compose("down -v --rmi all")
        print(f"{Colors.BLUE}🧹 Pruning dangling volumes and images...{Colors.ENDC}")
        self.run_command("docker volume prune -f")
        self.run_command("docker image prune -f")

    def run_docker_validation(self, ci_mode: bool = False) -> bool:
        self.print_step(f"Starting Docker Validation (Isolated Project: {TEST_PROJECT_NAME})")

        success, _ = self.run_command("docker info", capture_output=True)
        if not success:
            self.print_error("Docker is not running. Please start Docker Desktop.")
            return False

        if not COMPOSE_FILE.exists():
            self.print_error(f"Compose file not found at {COMPOSE_FILE}")
            return False

        # Ensure a clean slate before starting
        self.cleanup_docker()

        try:
            self.print_step("Building Docker images (no-cache)")
            # Set capture_output=False to show build progress to the user
            if not self.docker_compose("build --no-cache", capture_output=False)[0]:
                self.print_docker_logs()
                return False

            self.print_step("Starting containers")
            if not self.docker_compose("up -d", capture_output=False)[0]:
                self.print_docker_logs()
                return False

            # Dynamic wait for health
            if not self.wait_for_services_healthy(timeout=240):
                self.print_docker_logs()
                return False

            self.print_step("Verifying all containers are running")
            success, ps_out = self.docker_compose("ps --format json")
            if success and ps_out:
                try:
                    containers = []
                    lines = [L for L in ps_out.strip().split("\n") if L.strip()]
                    for line in lines:
                        try:
                            data = json.loads(line)
                            if isinstance(data, list):
                                containers.extend(data)
                            else:
                                containers.append(data)
                        except json.JSONDecodeError:
                            continue

                    failed_services = []
                    for c in containers:
                        state = str(c.get("State", "")).lower() or str(c.get("Status", "")).lower()
                        service_name = c.get("Service", "unknown")
                        if "running" not in state and "healthy" not in state:
                            failed_services.append(service_name)

                    if failed_services:
                        self.print_error(f"The following services failed to start: {', '.join(failed_services)}")
                        if not ci_mode:
                            for service in failed_services:
                                print(f"\n{Colors.CYAN}Logs for {service}:{Colors.ENDC}")
                                _, logs = self.docker_compose(f"logs --tail=20 {service}")
                                print(logs)
                        return False

                    if containers:
                        self.print_success("All containers are running/healthy")
                except Exception as e:
                    print(f"{Colors.BLUE}Warning: Could not parse docker-compose ps output: {e}{Colors.ENDC}")

            # Backend specific checks
            env = os.environ.copy()
            env["CONTAINER_PREFIX"] = TEST_PROJECT_NAME
            _, output = self.run_command(
                f"docker compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} ps -q backend", capture_output=True, env=env
            )
            container_id = output.strip() if output else None
            if not container_id:
                self.print_error("Backend container not found")
                return False

            self.print_step("Checking backend process")
            success, ps_out = self.run_command(f"docker exec {container_id} ps aux", capture_output=True)
            if not any(x in ps_out for x in ["manage.py", "gunicorn"]):
                self.print_error("Backend process not found")
                return False

            commands = [
                ("Updating content", "python manage.py update_all_content"),
                ("Django system check", "python manage.py check"),
                ("Checking migrations", "python manage.py showmigrations --plan"),
            ]

            for desc, cmd in commands:
                self.print_step(f"Docker | {desc}")
                success, out = self.run_command(f"docker exec {container_id} {cmd}", capture_output=True)
                if not success:
                    self.print_error(f"Command failed: {cmd}\n{out}")
                    return False
                self.print_success(f"{desc} passed")

            return True

        finally:
            self.cleanup_docker()

    def extra_checks(self) -> bool:
        """Run standard extra commands and then run Docker validation."""
        if not super().extra_checks():
            return False

        # If --all is passed, we check if user wants to run Docker tests (similar to test stages)
        # or just run it directly if in CI mode.
        ci_mode = "--ci" in sys.argv
        if ci_mode:
            return self.run_docker_validation(ci_mode=True)

        prompt = f"\n{Colors.BLUE}🚀 Run Full Docker Validation? [y/N]: {Colors.ENDC}"
        try:
            answer = input(prompt).strip().lower()
        except EOFError:
            answer = "n"

        if answer == "y":
            return self.run_docker_validation(ci_mode=False)

        self.print_skip("Skipping Docker validation.")
        return True

    def run_ci(self) -> None:
        """Override CI gate to ensure tests run BEFORE heavy Docker validation."""
        self._clear_screen()

        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.config.project_name} CI gate ==={Colors.ENDC}")

        # 1. Static analysis
        if not self.check_quality():
            sys.exit(1)
        if not self.check_types():
            sys.exit(1)
        if not self.check_security():
            sys.exit(1)

        # 2. Fast tests (Unit, Integration)
        for stage in self.config.test_stages:
            if not self.run_tests(stage):
                sys.exit(1)

        # 3. Heavy validation (Docker)
        if not self.extra_checks():
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CI CHECKS PASSED!{Colors.ENDC}")

    def run_all(self) -> None:
        """Override to run unit tests BEFORE heavy Docker validation."""
        self._clear_screen()

        if not self.check_quality():
            sys.exit(1)
        if not self.check_types():
            sys.exit(1)
        if not self.check_security():
            sys.exit(1)

        # Run configured test stages (unit, integration, etc.) first
        if not self._run_auto_test_stages():
            sys.exit(1)
        if not self._run_prompted_test_stages():
            sys.exit(1)

        # Finally run extra checks (Docker validation)
        if not self.extra_checks():
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")


if __name__ == "__main__":
    LilyCheckRunner(PROJECT_ROOT).main()
