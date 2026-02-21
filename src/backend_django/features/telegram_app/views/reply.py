import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from features.main.models.contact_request import ContactRequest

from ..decorators import tma_secure_required
from ..services.notification import NotificationService


# We exempt CSRF because TMA might POST without standard Django CSRF token,
# but we rely on Telegram's initData and HMAC for security.
@csrf_exempt
@tma_secure_required
def reply_form_view(request):
    """
    Renders the TMA reply form on GET.
    Accepts form submission on POST and enqueues the email task.
    """
    req_id = request.GET.get("req_id") or request.POST.get("req_id")

    if request.method == "POST":
        try:
            # Try to parse JSON data if submitted via JS fetch
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        reply_text = data.get("reply_text", "").strip()
        subject = data.get("subject", "Re: Your Request")

        if not reply_text:
            return JsonResponse({"status": "error", "message": "Reply text is required"}, status=400)

        try:
            contact_req = ContactRequest.objects.get(id=req_id)
            recipient_email = contact_req.client.email
            if not recipient_email:
                return JsonResponse({"status": "error", "message": "Client has no email address"}, status=400)
        except ContactRequest.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Request not found"}, status=404)

        # Enqueue the email sending task with full data
        success = NotificationService.enqueue_reply_email(
            request_id=req_id, recipient_email=recipient_email, reply_text=reply_text, subject=subject
        )

        if success:
            contact_req.is_processed = True
            contact_req.save(update_fields=["is_processed"])
            return JsonResponse({"status": "success", "message": "Reply queued successfully"})
        else:
            return JsonResponse({"status": "error", "message": "Failed to queue reply"}, status=500)

    # For GET: render the form template
    context = {
        "req_id": req_id,
        # We also pass the URL parameters so the form can include them
        # if needed (e.g. signature). But TMA handles most via initData.
        "ts": request.GET.get("ts"),
        "sig": request.GET.get("sig"),
    }
    return render(request, "telegram_app/reply_form.html", context)
