from __future__ import annotations

from typing import Any

from django.shortcuts import redirect
from django.views.generic import TemplateView
from system.services.worker_ops import WorkerOpsService

from cabinet.mixins import StaffRequiredMixin


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
