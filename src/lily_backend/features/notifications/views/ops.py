from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from ..models import NotificationLog


@permission_required("system.view_sitesettings")
def log_view(request):
    """View notification logs in the ops section of the cabinet."""
    logs = NotificationLog.objects.all()[:100]  # Show recent 100 logs
    return render(request, "features/notifications/log.html", {"logs": logs})
