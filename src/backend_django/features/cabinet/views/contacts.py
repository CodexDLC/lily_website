"""Contact requests list view (Admin only)."""

from core.logger import log
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.contact_request import ContactRequest


class ContactRequestsView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/contacts/list.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: ContactRequestsView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "contacts"

        # Get all requests ordered by date, newest first
        requests = ContactRequest.objects.select_related("client").order_by("-created_at")
        ctx["requests"] = requests

        # Count unprocessed for badge
        ctx["unprocessed_count"] = requests.filter(is_processed=False).count()

        log.info(f"View: ContactRequestsView | Action: Success | total_requests={requests.count()}")
        return ctx

    def post(self, request, *args, **kwargs):
        """Handle HTMX actions for individual contact requests."""
        request_id = request.POST.get("request_id")
        action = request.POST.get("action")

        log.info(f"View: ContactRequestsView | Action: {action} | request_id={request_id} | user={request.user.id}")

        contact_request = get_object_or_404(ContactRequest, pk=request_id)

        try:
            if action == "toggle_processed":
                contact_request.is_processed = not contact_request.is_processed
                contact_request.save(update_fields=["is_processed", "updated_at"])
                log.debug(
                    f"View: ContactRequestsView | Action: StatusToggled | is_processed={contact_request.is_processed}"
                )

            elif action == "save_notes":
                notes = request.POST.get("admin_notes", "").strip()
                contact_request.admin_notes = notes
                contact_request.save(update_fields=["admin_notes", "updated_at"])
                log.debug("View: ContactRequestsView | Action: NotesSaved")

        except Exception as e:
            log.error(f"View: ContactRequestsView | Action: PostFailed | error={e}")
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

        # Instead of JsonResponse, we render the row template so HTMX swaps just that row
        # This is standard HTMX pattern

        ctx = self.get_context_data()
        ctx["req"] = contact_request  # pass the single object to the row template

        from django.http import HttpResponse
        from django.template.loader import render_to_string

        html = render_to_string("cabinet/contacts/row.html", ctx, request=request)
        return HttpResponse(html)

    def delete(self, request, *args, **kwargs):
        """Handle deletion of a contact request via HTMX."""
        # Note: HTMX DELETE requests usually pass data in the URL or body depending on setup.
        # Let's assume the ID is in the query params for DELETE or we extract it.
        # Actually, standard HTMX delete puts it in the URL if built that way.
        pass  # Will implement later if needed, starting with just processed toggle.
