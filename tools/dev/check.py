"""Quality gate for Lily Project."""

import json
import os
import sys
import time
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

    def docker_compose(self, args: str) -> tuple[bool, str]:
        env = os.environ.copy()
        env["CONTAINER_PREFIX"] = TEST_PROJECT_NAME
        cmd = f"docker compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} {args}"
        return self.run_command(cmd, env=env)

    def cleanup_docker(self) -> None:
        print(f"\n{Colors.BLUE}🧹 Cleaning up Docker resources (Project: {TEST_PROJECT_NAME})...{Colors.ENDC}")
        self.docker_compose("down -v")
        print(f"{Colors.BLUE}🧹 Pruning dangling volumes...{Colors.ENDC}")
        self.run_command("docker volume prune -f")

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
            if not self.docker_compose("build --no-cache")[0]:
                return False

            self.print_step("Starting containers")
            if not self.docker_compose("up -d")[0]:
                return False

            self.print_step("Waiting for services to be ready (15s)")
            time.sleep(15)

            self.print_step("Verifying all containers are running")
            success, ps_out = self.docker_compose("ps --format json")
            if success and ps_out:
                try:
                    containers = []
                    lines = ps_out.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
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
                    print(f"{Colors.YELLOW}Warning: Could not parse docker-compose ps output: {e}{Colors.ENDC}")

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

        prompt = f"\n{Colors.YELLOW}🚀 Run Full Docker Validation? [y/N]: {Colors.ENDC}"
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
        # Clear screen for fresh output
        os.system("cls" if os.name == "nt" else "clear")

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
        # Clear screen for fresh output
        os.system("cls" if os.name == "nt" else "clear")

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
