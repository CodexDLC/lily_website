import os
import sys

# Добавляем путь к backend_django в PYTHONPATH
sys.path.append(os.path.join(os.getcwd(), "src", "backend_django"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")

import django

django.setup()

try:
    print("Testing Django imports...")
    print("SUCCESS: AdminDashboardManager imported!")

    print("SUCCESS: DashboardRefreshService imported!")

    print("SUCCESS: admin_router imported!")

except Exception as e:
    print(f"FAILURE: Django import test failed: {e}")
    import traceback

    traceback.print_exc()
