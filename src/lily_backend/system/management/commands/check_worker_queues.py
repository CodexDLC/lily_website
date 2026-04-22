from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand

from system.services.worker_ops import WorkerOpsService


class Command(BaseCommand):
    help = "Check ARQ worker self-scheduling registry health."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON.")

    def handle(self, *args: Any, **options: Any) -> None:
        summary = WorkerOpsService().summary()
        if options["as_json"]:
            self.stdout.write(
                json.dumps(
                    {
                        **{key: value for key, value in summary.items() if key != "tasks"},
                        "tasks": [task.__dict__ for task in summary["tasks"]],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            self.stdout.write(f"Worker queues: {summary['status']}")
            for task in summary["tasks"]:
                self.stdout.write(
                    f"- {task.task_id} [{task.health}] queue={task.queue_name or '-'} "
                    f"status={task.last_status} failures={task.consecutive_failures}"
                )

        status = summary["status"]
        if status == "critical":
            raise SystemExit(2)
        if status == "degraded":
            raise SystemExit(1)
