from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import NotificationRecipient


@require_POST
@permission_required("system.change_sitesettings")
def toggle_recipient(request, pk):
    """Toggle the enabled state of a recipient."""
    try:
        recipient = NotificationRecipient.objects.get(pk=pk)
        recipient.enabled = not recipient.enabled
        recipient.save()
    except NotificationRecipient.DoesNotExist:
        pass

    # Redirect back to the site settings page with the partial-tab activated
    url = reverse("cabinet:site-settings") + "#notifications-tab"
    return redirect(url)


@require_POST
@permission_required("system.change_sitesettings")
def add_recipient(request):
    """Add a new recipient."""
    email = request.POST.get("email", "").strip()
    name = request.POST.get("name", "").strip()
    kind = request.POST.get("kind", NotificationRecipient.KIND_ADMIN)

    if email:
        NotificationRecipient.objects.get_or_create(email=email, defaults={"name": name, "kind": kind, "enabled": True})

    url = reverse("cabinet:site-settings") + "#notifications-tab"
    return redirect(url)


@require_POST
@permission_required("system.change_sitesettings")
def delete_recipient(request, pk):
    """Delete a recipient."""
    NotificationRecipient.objects.filter(pk=pk).delete()

    url = reverse("cabinet:site-settings") + "#notifications-tab"
    return redirect(url)
