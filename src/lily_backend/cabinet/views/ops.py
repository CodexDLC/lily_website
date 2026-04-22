from __future__ import annotations

import io
import sys
from typing import Any

from core.logger import logger
from django.core.management import call_command
from django.shortcuts import redirect
from django.views.generic import TemplateView
from system.services.worker_ops import WorkerOpsService

from cabinet.mixins import StaffRequiredMixin


class ConsoleTee:
    """Write command output to both the UI log buffer and container stdout/stderr."""

    def __init__(self, buffer: io.StringIO, stream: Any) -> None:
        self.buffer = buffer
        self.stream = stream

    def write(self, value: str) -> int:
        self.buffer.write(value)
        return self.stream.write(value)

    def flush(self) -> None:
        self.buffer.flush()
        self.stream.flush()


class DataMaintenanceView(StaffRequiredMixin, TemplateView):
    template_name = "cabinet/ops/maintenance.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        # Extra security: Only superusers can manage data
        if not request.user.is_superuser:
            return redirect("cabinet:analytics_dashboard")

        request.cabinet_module = "ops"
        request.cabinet_space = "staff"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Check if we have logs from previous execution in session
        context["execution_log"] = self.request.session.pop("maintenance_log", None)
        return context

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        action = request.POST.get("action", "")
        output = io.StringIO()
        stdout = ConsoleTee(output, sys.stdout)
        stderr = ConsoleTee(output, sys.stderr)

        commands_map: dict[str, tuple[str, dict[str, Any]]] = {
            "sync_catalog": ("load_catalog", {}),
            "sync_content": ("update_all_content", {}),
            "migrate_users": ("migrate_users", {}),
            "migrate_clients": ("migrate_clients", {}),
            "migrate_appointments": ("migrate_appointments", {}),
            "migrate_all": ("migrate_all_legacy", {}),
        }

        if action not in commands_map:
            logger.warning(
                f"Cabinet maintenance action ignored: action={action!r} post_keys={list(request.POST.keys())}"
            )
            return redirect("cabinet:ops_maintenance")

        cmd, cmd_kwargs = commands_map[action]
        logger.info(f"Cabinet maintenance action started: action={action} command={cmd}")
        try:
            call_command(cmd, stdout=stdout, stderr=stderr, **cmd_kwargs)
            request.session["maintenance_log"] = output.getvalue()
            logger.info(f"Cabinet maintenance action completed: action={action} command={cmd}")
        except Exception as e:
            request.session["maintenance_log"] = f"CRITICAL ERROR: {str(e)}\n\n{output.getvalue()}"
            logger.exception(f"Cabinet maintenance action failed: action={action} command={cmd}")

        return redirect("cabinet:ops_maintenance")


class WorkerOpsView(StaffRequiredMixin, TemplateView):
    template_name = "cabinet/ops/workers.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "ops"
        request.cabinet_space = "staff"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(WorkerOpsService().summary())
        return context

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        service = WorkerOpsService()
        task_id = request.POST.get("task_id", "")
        action = request.POST.get("action", "")
        if action == "enable":
            service.set_enabled(task_id, True)
        elif action == "disable":
            service.set_enabled(task_id, False)
        elif action == "run_now":
            service.enqueue_now(task_id)
        elif action == "reschedule":
            service.enqueue_now(task_id, defer_by=60)
        return redirect("cabinet:ops_workers")
