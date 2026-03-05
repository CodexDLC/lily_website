"""Contact Requests CRM view (Admin only)."""

from datetime import datetime

from core.logger import log
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.contact_request import ContactRequest
from features.system.services.notification import NotificationService


class ContactRequestsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/crm/contacts/list.html"

    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        req_id = request.GET.get("id")

        if action and req_id:
            req = get_object_or_404(ContactRequest, id=req_id)
            if action == "view":
                return render(request, "cabinet/crm/contacts/_detail_view.html", {"req": req})
            if action == "view_row":
                return render(request, "cabinet/crm/contacts/_single_card.html", {"req": req})
            if action == "toggle_status":
                req.is_processed = not req.is_processed
                req.save()
                log.info(f"CRM: ContactRequest {req.id} status toggled to {req.is_processed}")
                return render(request, "cabinet/crm/contacts/_single_card.html", {"req": req})

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        req_id = request.POST.get("id")
        new_reply = request.POST.get("new_reply", "").strip()

        if not req_id or not new_reply:
            log.warning(f"CRM: Invalid POST request | action={action} | id={req_id}")
            return self.get(request, *args, **kwargs)

        req = get_object_or_404(ContactRequest, id=req_id)
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

        if action == "send_email":
            # 1. Prepare history for the email
            history = f"--- Original Message ---\n{req.message}\n\n"
            if req.admin_notes:
                history += f"--- Previous Correspondence ---\n{req.admin_notes}"

            # 2. Update internal notes (Newest on top)
            new_note = f"[{timestamp}] SENT EMAIL:\n{new_reply}\n"
            separator = "\n" if req.admin_notes else ""
            req.admin_notes = new_note + separator + req.admin_notes
            req.is_processed = True
            req.save()

            # 3. Send Email via Universal Gateway
            if req.client.email:
                NotificationService.send_universal(
                    recipient_email=req.client.email,
                    template_name="ct_reply",
                    subject=f"Re: Your inquiry [Ref: #{req.id}]",
                    context_data={"reply_text": new_reply, "history_text": history, "request_id": req.id},
                    channels=["email"],
                )
                log.info(f"CRM: Email response sent for Request {req.id}")

            return render(request, "cabinet/crm/contacts/_single_card.html", {"req": req})

        if action == "save_notes":
            new_note = f"[{timestamp}] NOTE:\n{new_reply}\n"
            separator = "\n" if req.admin_notes else ""
            req.admin_notes = new_note + separator + req.admin_notes
            req.is_processed = True
            req.save()
            log.info(f"CRM: Internal note saved for Request {req.id}")
            return render(request, "cabinet/crm/contacts/_single_card.html", {"req": req})

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "contacts"

        search = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "new")
        topic_filter = self.request.GET.get("topic", "all")

        qs = ContactRequest.objects.select_related("client").order_by("-created_at")

        if search:
            qs = qs.filter(
                Q(client__first_name__icontains=search)
                | Q(client__last_name__icontains=search)
                | Q(client__phone__icontains=search)
                | Q(message__icontains=search)
            )

        if status_filter == "new":
            qs = qs.filter(is_processed=False)
        elif status_filter == "processed":
            qs = qs.filter(is_processed=True)

        if topic_filter != "all":
            qs = qs.filter(topic=topic_filter)

        ctx["requests"] = qs
        ctx["search"] = search
        ctx["status_filter"] = status_filter
        ctx["topic_filter"] = topic_filter
        ctx["topic_choices"] = ContactRequest.TOPIC_CHOICES
        ctx["unprocessed_count"] = ContactRequest.objects.filter(is_processed=False).count()

        return ctx
