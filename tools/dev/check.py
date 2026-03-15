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
    # This handles warnings if requests is imported in this script
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


def print_step(msg):
    print(f"\n{Colors.YELLOW}🔍 {msg}...{Colors.ENDC}")


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")


def run_command(command, cwd=PROJECT_ROOT, capture_output=False, env=None):
    """Runs a system command and returns result."""
    current_env = os.environ.copy()

    # --- THE FIX: Silence warnings for ALL subprocesses ---
    # This prevents the "RequestsDependencyWarning" from showing up in Ruff, Mypy, etc.
    current_env["PYTHONWARNINGS"] = "ignore"

    if env:
        current_env.update(env)

    try:
        shell = isinstance(command, str)
        result = subprocess.run(
            command, cwd=cwd, shell=shell, check=True, text=True, capture_output=capture_output, env=current_env
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stdout if capture_output else str(e)


# --- Docker Helpers ---


def docker_compose(args):
    env = {"CONTAINER_PREFIX": TEST_PROJECT_NAME}
    cmd = f"docker-compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} {args}"
    return run_command(cmd, env=env)


def cleanup_docker():
    print(f"\n{Colors.BLUE}🧹 Cleaning up Docker resources (Project: {TEST_PROJECT_NAME})...{Colors.ENDC}")
    # 1. Останавливаем и удаляем контейнеры и их тома
    docker_compose("down -v")

    # 2. Удаляем все "висячие" (dangling) тома, которые накопились
    print(f"{Colors.BLUE}🧹 Pruning dangling volumes...{Colors.ENDC}")
    run_command("docker volume prune -f")


# --- Check Functions ---


def check_linters(ci_mode=False):
    print_step("Running Linters (Ruff & Pre-commit hooks)")

    # In CI, we only VERIFY. No auto-fixes allowed to ensure repository consistency.
    if not ci_mode:
        print("Attempting to auto-fix Ruff issues...")
        fix_success, _ = run_command(f"poetry run ruff check {PYTHON_DIRS} --fix", capture_output=False)
        if not fix_success:
            print_error("Ruff auto-fix command failed.")
            return False
        print_success("Ruff auto-fix completed.")

        print("Attempting to auto-format with Ruff...")
        format_success, _ = run_command(f"poetry run ruff format {PYTHON_DIRS}", capture_output=False)
        if not format_success:
            print_error("Ruff auto-format command failed.")
            return False
        print_success("Ruff auto-format completed.")

    # --- Verification checks (The only ones that run in CI) ---
    print("Verifying Ruff check...")
    ruff_check_success, ruff_check_out = run_command(f"poetry run ruff check {PYTHON_DIRS}", capture_output=True)
    if not ruff_check_success:
        print_error(f"Ruff check failed:\n{ruff_check_out}")
        return False
    print_success("Ruff check passed.")

    print("Verifying Ruff format...")
    ruff_format_check_success, ruff_format_check_out = run_command(
        f"poetry run ruff format {PYTHON_DIRS} --check", capture_output=True
    )
    if not ruff_format_check_success:
        print_error(f"Ruff format check failed:\n{ruff_format_check_out}")
        return False
    print_success("Ruff format check passed.")

    print("Running basic pre-commit hooks...")
    basic_hooks = [
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-json",
        "markdownlint",
        "bandit",
        "detect-secrets",
    ]
    for hook in basic_hooks:
        if not run_command(f"poetry run pre-commit run {hook} --all-files")[0]:
            print_error(f"Pre-commit hook '{hook}' failed")
            return False
    print_success("Basic pre-commit hooks passed.")

    return True


def check_types():
    print_step("Checking Types (Mypy)")
    cache_dir = PROJECT_ROOT / ".mypy_cache"
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)

    # Mypy should only check Python directories
    success, out = run_command(f"poetry run mypy {PYTHON_DIRS}", capture_output=True)
    if not success:
        print_error(f"Mypy check failed:\n{out}")
    return success


def run_tests():
    print_step("Running Unit Tests (Pytest)")
    os.environ["SECRET_KEY"] = "local_test_key"  # pragma: allowlist secret
    # Run ALL tests locally (removed -m unit filter)
    return run_command("poetry run pytest src -v")[0]


def check_security_deep():
    """Глубокий аудит безопасности: зависимости + статика."""
    print_step("Deep Security Audit")

    # Запускаем аудит зависимостей через poetry напрямую (дополнительная страховка)
    print("Checking for vulnerable dependencies...")
    success, out = run_command("poetry run pip-audit")
    if not success:
        print_error(f"Security vulnerabilities found in packages:\n{out}")
        return False

    # Запускаем Bandit для поиска дыр в логике (SQL инъекции, небезопасный random и т.д.)
    print("Running Bandit (SAST)...")
    success, out = run_command("poetry run bandit -r src/ -ll")
    if not success:
        print_error(f"Bandit found security risks:\n{out}")
        return False

    print_success("Security audit passed.")
    return True


def run_docker_validation(ci_mode=False):
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

        # --- New: Check all containers status ---
        print_step("Verifying all containers are running")
        success, ps_out = docker_compose("ps --format json")
        if success and ps_out:
            import json

            try:
                containers = []
                # Handle multiple JSON objects (one per line) or a single JSON list
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
                    # Status can be 'running', 'healthy', 'exited', etc.
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
                    else:
                        print(f"{Colors.YELLOW}Logs are hidden in CI mode to prevent secret leakage.{Colors.ENDC}")
                    return False

                if containers:
                    print_success("All containers are running/healthy")
                else:
                    print(f"{Colors.YELLOW}Warning: No containers found to check.{Colors.ENDC}")

            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not parse docker-compose ps output: {e}{Colors.ENDC}")

        # --- Backend specific checks ---
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


def run_all(with_docker=False, ci_mode=False):
    if not ci_mode:
        os.system("cls" if os.name == "nt" else "clear")

    if not check_linters(ci_mode=ci_mode):
        sys.exit(1)
    if not check_types():
        sys.exit(1)
    if not check_security_deep():
        sys.exit(1)

    # Prompt for tests
    test_choice = "y" if ci_mode else input(f"\n{Colors.YELLOW}🚀 Run Unit Tests? [y/N]: {Colors.ENDC}").strip().lower()

    if test_choice == "y":
        if not run_tests():
            sys.exit(1)
    else:
        print(f"{Colors.BLUE}ℹ️ Skipping Unit Tests.{Colors.ENDC}")

    # Prompt for Docker
    if with_docker:
        docker_choice = (
            "y"
            if ci_mode
            else input(f"\n{Colors.YELLOW}🐳 Run Full Docker Validation? [y/N]: {Colors.ENDC}").strip().lower()
        )

        if docker_choice == "y":
            if not run_docker_validation(ci_mode=ci_mode):
                sys.exit(1)
        else:
            print(f"{Colors.BLUE}ℹ️ Skipping Docker validation.{Colors.ENDC}")
    else:
        if not ci_mode:
            print(f"\n{Colors.BLUE}ℹ️ Docker validation skipped. Use --docker to enable the prompt.{Colors.ENDC}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED! You are ready to push.{Colors.ENDC}")


def interactive_menu():
    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}🛠 Lily Project Quality Tool{Colors.ENDC}")
        print("1. Fast Check (Lint only)")
        print("2. Type Check (Mypy)")
        print("3. Run Unit Tests")
        print("4. Full Docker Validation")
        print("5. Run Everything (Default, no Docker)")
        print("6. Run Everything (WITH Docker)")
        print("0. Exit")

        choice = input(f"\n{Colors.YELLOW}Select an option [5]: {Colors.ENDC}").strip() or "5"

        if choice == "1":
            check_linters()
        elif choice == "2":
            check_types()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            run_docker_validation()
        elif choice == "5":
            run_all(with_docker=False)
        elif choice == "6":
            run_all(with_docker=True)
        elif choice == "0":
            break
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lily Project Quality Checker")
    parser.add_argument("--settings", action="store_true", help="Open interactive menu")
    parser.add_argument("--docker", action="store_true", help="Include Docker build validation")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (non-interactive, all checks)")
    args = parser.parse_args()

    try:
        if args.settings:
            interactive_menu()
        else:
            # In CI mode, we always want docker validation
            run_all(with_docker=(args.docker or args.ci), ci_mode=args.ci)
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Aborted by user.{Colors.ENDC}")
        sys.exit(1)
