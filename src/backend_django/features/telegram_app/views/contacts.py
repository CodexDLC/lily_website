import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from features.main.models.contact_request import ContactRequest
from features.system.services.dashboard_refresh_service import DashboardRefreshService
from loguru import logger as log

from ..decorators import tma_secure_required


@csrf_exempt
@tma_secure_required
def contacts_view(request):
    """
    Renders the TMA contacts list and handles AJAX actions.
    """
    req_id = request.GET.get("req_id") or request.POST.get("req_id")
    ts = request.GET.get("ts") or request.POST.get("ts")
    sig = request.GET.get("sig") or request.POST.get("sig")

    # Handle AJAX Actions (Read / Delete)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        action = data.get("action")
        contact_id = data.get("contact_id")

        if not action or not contact_id:
            return JsonResponse({"status": "error", "message": "Missing action or contact_id"}, status=400)

        try:
            contact = ContactRequest.objects.get(id=contact_id)

            if action == "read":
                contact.is_processed = True
                contact.save()
                log.info(f"TMA Contacts | Contact {contact_id} marked as read")
                # Trigger dashboard refresh asynchronously if possible, or await it
                # DashboardRefreshService.refresh_all() is async, so we need to run it in event loop
                # Django 4.2+ async views vs sync views compat:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(DashboardRefreshService.refresh_all())
                except RuntimeError:
                    asyncio.run(DashboardRefreshService.refresh_all())

                return JsonResponse({"status": "success", "message": "Contact marked as read"})

            elif action == "delete":
                contact.delete()
                log.info(f"TMA Contacts | Contact {contact_id} deleted")
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(DashboardRefreshService.refresh_all())
                except RuntimeError:
                    asyncio.run(DashboardRefreshService.refresh_all())

                return JsonResponse({"status": "success", "message": "Contact deleted"})

            else:
                return JsonResponse({"status": "error", "message": "Invalid action"}, status=400)

        except ContactRequest.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Contact not found"}, status=404)
        except Exception as e:
            log.error(f"TMA Contacts | Error processing action {action}: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # GET Request: Render the corresponding tab
    tab = request.GET.get("tab", "general")
    is_archive = tab == "archive"

    if is_archive:
        contacts = ContactRequest.objects.filter(is_processed=True).order_by("-created_at")
    else:
        contacts = ContactRequest.objects.filter(is_processed=False, topic=tab).order_by("-created_at")

    context = {
        "req_id": req_id,
        "ts": ts,
        "sig": sig,
        "tab": tab,
        "is_archive": is_archive,
        "contacts": contacts,
    }
    return render(request, "telegram_app/contacts.html", context)
