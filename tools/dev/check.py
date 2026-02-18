import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "deploy" / "docker-compose.yml"
TEST_PROJECT_NAME = "lily-quality-check"  # Уникальное имя для изоляции тестов


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
    # Передаем CONTAINER_PREFIX для уникальных имен контейнеров
    env = {"CONTAINER_PREFIX": TEST_PROJECT_NAME}
    cmd = f"docker-compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} {args}"
    return run_command(cmd, env=env)


def cleanup_docker():
    print(f"\n{Colors.BLUE}🧹 Cleaning up Docker resources (Project: {TEST_PROJECT_NAME})...{Colors.ENDC}")
    docker_compose("down -v")


# --- Check Functions ---


def check_linters():
    print_step("Running Linters (Pre-commit & Ruff)")
    hooks = ["trailing-whitespace", "end-of-file-fixer", "check-yaml", "ruff-format", "ruff"]
    return all(run_command(f"pre-commit run {hook} --all-files")[0] for hook in hooks)


def check_types():
    print_step("Checking Types (Mypy)")
    cache_dir = PROJECT_ROOT / ".mypy_cache"
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)
    return run_command("mypy src/")[0]


def run_tests():
    print_step("Running Unit Tests (Pytest)")
    os.environ["SECRET_KEY"] = "local_test_key"
    return run_command("pytest src -m unit -v")[0]


def run_docker_validation():
    print_step(f"Starting Docker Validation (Isolated Project: {TEST_PROJECT_NAME})")

    # 1. Check Docker daemon
    success, _ = run_command("docker info", capture_output=True)
    if not success:
        print_error("Docker is not running. Please start Docker Desktop.")
        return False

    # 2. Check Compose file
    if not COMPOSE_FILE.exists():
        print_error(f"Compose file not found at {COMPOSE_FILE}")
        return False

    try:
        # 3. Build
        print_step("Building Docker images (no-cache)")
        if not docker_compose("build --no-cache")[0]:
            return False

        # 4. Up
        print_step("Starting containers")
        if not docker_compose("up -d")[0]:
            return False

        # 5. Wait
        print_step("Waiting for services to be ready (15s)")
        time.sleep(15)

        # 6. Get Backend Container ID
        env = {"CONTAINER_PREFIX": TEST_PROJECT_NAME}
        _, output = run_command(
            f"docker-compose -p {TEST_PROJECT_NAME} -f {COMPOSE_FILE} ps -q backend", capture_output=True, env=env
        )
        container_id = output.strip()
        if not container_id:
            print_error("Backend container not found")
            return False

        # 7. Check Process
        print_step("Checking backend process (Gunicorn/Manage)")
        success, ps_out = run_command(f"docker exec {container_id} ps aux", capture_output=True)
        if not any(x in ps_out for x in ["manage.py", "gunicorn"]):
            print_error("Backend process not found in container")
            return False
        print_success("Backend process is running")

        # 8. Run Django Commands
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
            if "showmigrations" in cmd and "[ ]" in out:
                print_error("Found unapplied migrations!")
                return False
            print_success(f"{desc} passed")

        return True

    finally:
        cleanup_docker()


# --- Main Logic ---


def run_all():
    os.system("cls" if os.name == "nt" else "clear")
    if not check_linters():
        sys.exit(1)
    if not check_types():
        sys.exit(1)
    if not run_tests():
        sys.exit(1)
    if not run_docker_validation():
        sys.exit(1)

    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED! You are ready to push.{Colors.ENDC}")


def interactive_menu():
    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}🛠 Lily Project Quality Tool{Colors.ENDC}")
        print("1. Fast Check (Lint only)")
        print("2. Type Check (Mypy)")
        print("3. Run Unit Tests")
        print("4. Full Docker Validation")
        print("5. Run Everything (Default)")
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
            run_all()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lily Project Quality Checker")
    parser.add_argument("--settings", action="store_true", help="Open interactive menu")
    args = parser.parse_args()

    try:
        if args.settings:
            interactive_menu()
        else:
            run_all()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Aborted by user.{Colors.ENDC}")
        sys.exit(1)
