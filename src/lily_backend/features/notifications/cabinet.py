from codex_django.cabinet import declare

declare(
    space="staff",
    module="ops",
    namespace="notifications",
    title="Notification Logs",
    icon="heroicons:bell-alert",
    path="ops/notifications/",
    view="features.notifications.views.ops.log_view",
    permission="system.view_sitesettings",  # Restrict to admins/ops
)
