import argparse
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "deploy" / "docker-compose.test.yml"
TEST_PROJECT_NAME = "lily-quality-check"

# Directories to check for Python tools (Ruff, Mypy)
PYTHON_DIRS = "src/ tools/"

# --- Silence non-critical warnings in CURRENT process ---
try:
    from requests.exceptions import RequestsDependencyWarning

    warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
except ImportError:
    pass


# ANSI Colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_step(msg: str) -> None:
    print(f"\n{Colors.YELLOW}🔍 {msg}...{Colors.ENDC}")


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")


def run_command(
    command: str, cwd: Path = PROJECT_ROOT, capture_output: bool = False, env: dict | None = None
) -> tuple[bool, str]:
    """Runs a system command and returns result."""
    current_env = os.environ.copy()
    current_env["PYTHONWARNINGS"] = "ignore"
    if env:
        current_env.update(env)

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=False,
            text=True,
            capture_output=capture_output,
            env=current_env,
        )
        return result.returncode == 0, result.stdout or result.stderr or ""
    except Exception as e:
        return False, str(e)


# --- Docker Helpers ---


def docker_compose(args: str) -> tuple[bool, str]:
    env = {"CONTAINER_PREFIX": TEST_PROJECT_NAME}
    cmd = f"docker-compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} {args}"
    return run_command(cmd, env=env)


def cleanup_docker() -> None:
    print(f"\n{Colors.BLUE}🧹 Cleaning up Docker resources (Project: {TEST_PROJECT_NAME})...{Colors.ENDC}")
    docker_compose("down -v")
    print(f"{Colors.BLUE}🧹 Pruning dangling volumes...{Colors.ENDC}")
    run_command("docker volume prune -f")


# --- Check Functions ---


def check_linters(ci_mode: bool = False) -> bool:
    print_step("Running Linters (Ruff & Pre-commit hooks)")

    if not ci_mode:
        print("Attempting to auto-fix Ruff issues...")
        run_command(f"poetry run ruff check {PYTHON_DIRS} --fix")
        print("Attempting to auto-format with Ruff...")
        run_command(f"poetry run ruff format {PYTHON_DIRS}")

    print("Verifying Ruff check...")
    success, out = run_command(f"poetry run ruff check {PYTHON_DIRS}", capture_output=True)
    if not success:
        print_error(f"Ruff check failed:\n{out}")
        return False
    print_success("Ruff check passed.")

    print("Verifying Ruff format...")
    success, out = run_command(f"poetry run ruff format {PYTHON_DIRS} --check", capture_output=True)
    if not success:
        print_error(f"Ruff format check failed:\n{out}")
        return False
    print_success("Ruff format check passed.")

    print("Running basic pre-commit hooks...")
    hooks = [
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-json",
        "markdownlint",
        "bandit",
        "detect-secrets",
    ]
    for hook in hooks:
        if not run_command(f"poetry run pre-commit run {hook} --all-files")[0]:
            print_error(f"Pre-commit hook '{hook}' failed")
            return False
    print_success("Basic pre-commit hooks passed.")

    return True


def check_types() -> bool:
    print_step("Checking Types (Mypy)")
    cache_dir = PROJECT_ROOT / ".mypy_cache"
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)

    success, out = run_command(f"poetry run mypy {PYTHON_DIRS}", capture_output=True)
    if not success:
        print_error(f"Mypy check failed:\n{out}")
    else:
        print_success("Mypy check passed.")
    return success


def check_security_deep() -> bool:
    print_step("Deep Security Audit")

    print("Checking for vulnerable dependencies (pip-audit)...")
    success, out = run_command("poetry run pip-audit", capture_output=True)
    if not success:
        print_error(f"Security vulnerabilities found in packages:\n{out}")
        return False

    print("Running Bandit (SAST)...")
    success, out = run_command("poetry run bandit -r src/ -ll", capture_output=True)
    if not success:
        print_error(f"Bandit found security risks:\n{out}")
        return False

    print_success("Security audit passed.")
    return True


def run_tests(marker: str = "unit") -> bool:
    """Runs tests with specific marker. 'unit' runs everything NOT marked as 'integration'."""
    print_step(f"Running {marker.capitalize()} Tests (Pytest)")
    os.environ["SECRET_KEY"] = "local_test_key"  # pragma: allowlist secret

    if marker == "unit":
        cmd = 'poetry run pytest src -m "not integration" -v --tb=short'
    else:
        cmd = f"poetry run pytest src -m {marker} -v --tb=short"

    success, out = run_command(cmd, capture_output=True)
    if success:
        print_success(f"{marker.capitalize()} tests passed.")
    else:
        print_error(f"{marker.capitalize()} tests failed:\n{out}")
    return success


def run_docker_validation(ci_mode: bool = False) -> bool:
    print_step(f"Starting Docker Validation (Isolated Project: {TEST_PROJECT_NAME})")

    success, _ = run_command("docker info", capture_output=True)
    if not success:
        print_error("Docker is not running. Please start Docker Desktop.")
        return False

    if not COMPOSE_FILE.exists():
        print_error(f"Compose file not found at {COMPOSE_FILE}")
        return False

    try:
        print_step("Building Docker images (no-cache)")
        if not docker_compose("build --no-cache")[0]:
            return False

        print_step("Starting containers")
        if not docker_compose("up -d")[0]:
            return False

        print_step("Waiting for services to be ready (15s)")
        time.sleep(15)

        print_step("Verifying all containers are running")
        success, ps_out = docker_compose("ps --format json")
        if success and ps_out:
            import json

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
                    print_error(f"The following services failed to start: {', '.join(failed_services)}")
                    if not ci_mode:
                        for service in failed_services:
                            print(f"\n{Colors.CYAN}Logs for {service}:{Colors.ENDC}")
                            _, logs = docker_compose(f"logs --tail=20 {service}")
                            print(logs)
                    return False

                if containers:
                    print_success("All containers are running/healthy")
            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not parse docker-compose ps output: {e}{Colors.ENDC}")

        # Backend specific checks
        env = {"CONTAINER_PREFIX": TEST_PROJECT_NAME}
        _, output = run_command(
            f"docker-compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} ps -q backend", capture_output=True, env=env
        )
        container_id = output.strip() if output else None
        if not container_id:
            print_error("Backend container not found")
            return False

        print_step("Checking backend process")
        success, ps_out = run_command(f"docker exec {container_id} ps aux", capture_output=True)
        if not any(x in ps_out for x in ["manage.py", "gunicorn"]):
            print_error("Backend process not found")
            return False

        commands = [
            ("Updating content", "python manage.py update_all_content"),
            ("Django system check", "python manage.py check"),
            ("Checking migrations", "python manage.py showmigrations --plan"),
        ]

        for desc, cmd in commands:
            print_step(f"Docker | {desc}")
            success, out = run_command(f"docker exec {container_id} {cmd}", capture_output=True)
            if not success:
                print_error(f"Command failed: {cmd}\n{out}")
                return False
            print_success(f"{desc} passed")

        return True

    finally:
        cleanup_docker()


# --- Main Logic ---


def run_all(with_docker: bool = False, ci_mode: bool = False) -> None:
    if not ci_mode:
        os.system("cls" if os.name == "nt" else "clear")

    print(f"{Colors.HEADER}{Colors.BOLD}=== Lily Project Quality Gate ==={Colors.ENDC}")

    if not check_linters(ci_mode=ci_mode):
        sys.exit(1)
    if not check_types():
        sys.exit(1)
    if not check_security_deep():
        sys.exit(1)

    # Unit Tests
    if (
        ci_mode or input(f"\n{Colors.YELLOW}🚀 Run Unit Tests? [y/N]: {Colors.ENDC}").strip().lower() == "y"
    ) and not run_tests("unit"):
        sys.exit(1)

    # Integration Tests
    if (
        ci_mode
        or input(f"\n{Colors.YELLOW}🧪 Run Integration Tests? (Requires Mailpit) [y/N]: {Colors.ENDC}").strip().lower()
        == "y"
    ) and not run_tests("integration"):
        sys.exit(1)

    # Docker Validation
    if with_docker:
        if (
            ci_mode
            or input(f"\n{Colors.YELLOW}🐳 Run Full Docker Validation? [y/N]: {Colors.ENDC}").strip().lower() == "y"
        ) and not run_docker_validation(ci_mode=ci_mode):
            sys.exit(1)
    elif not ci_mode:
        print(f"\n{Colors.BLUE}ℹ️ Docker validation skipped. Use --docker to enable the prompt.{Colors.ENDC}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED!{Colors.ENDC}")


def interactive_menu() -> None:
    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}🛠 Lily Project Quality Tool{Colors.ENDC}")
        print("1. Fast Check (Lint only)")
        print("2. Type Check (Mypy)")
        print("3. Run Unit Tests")
        print("4. Run Integration Tests (Requires Mailpit)")
        print("5. Deep Security Audit")
        print("6. Full Docker Validation")
        print("7. Run Everything (No Docker)")
        print("8. Run Everything (WITH Docker)")
        print("0. Exit")

        choice = input(f"\n{Colors.YELLOW}Select an option [7]: {Colors.ENDC}").strip() or "7"

        if choice == "1":
            check_linters()
        elif choice == "2":
            check_types()
        elif choice == "3":
            run_tests("unit")
        elif choice == "4":
            run_tests("integration")
        elif choice == "5":
            check_security_deep()
        elif choice == "6":
            run_docker_validation()
        elif choice == "7":
            run_all(with_docker=False)
        elif choice == "8":
            run_all(with_docker=True)
        elif choice == "0":
            break
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lily Project Quality Checker")
    parser.add_argument("--menu", action="store_true", help="Open interactive menu")
    parser.add_argument("--docker", action="store_true", help="Include Docker validation")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (non-interactive, all checks)")
    parser.add_argument("--tests", choices=["unit", "integration", "all"], help="Run specific test markers")

    args = parser.parse_args()

    try:
        if args.menu:
            interactive_menu()
        elif args.tests:
            if args.tests == "all":
                u = run_tests("unit")
                i = run_tests("integration")
                sys.exit(0 if u and i else 1)
            else:
                sys.exit(0 if run_tests(args.tests) else 1)
        else:
            run_all(with_docker=(args.docker or args.ci), ci_mode=args.ci)
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Aborted.{Colors.ENDC}")
        sys.exit(1)
