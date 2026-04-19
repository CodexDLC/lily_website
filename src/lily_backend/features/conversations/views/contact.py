from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.generic import FormView

from ..forms import ContactForm
from ..models import Message


class ContactFormView(FormView):
    template_name = "features/conversations/contacts.html"
    form_class = ContactForm

    def get_success_url(self):
        return self.request.path + "?sent=1"

    def _is_htmx(self):
        return self.request.headers.get("HX-Request") == "true"

    def form_valid(self, form):
        message = form.save(commit=False)
        message.source = Message.Source.CONTACT_FORM
        message.channel = Message.Channel.EMAIL
        message.save()

        # Save marketing consent to Client profile if provided
        consent_marketing = form.cleaned_data.get("consent_marketing", False)
        sender_email = form.cleaned_data.get("sender_email")

        from django.utils import timezone
        from system.models import Client

        # Try to find a client by email or use the logged-in user's client profile
        client = None
        if self.request.user.is_authenticated:
            client = getattr(self.request.user, "client_profile", None)

        if not client and sender_email:
            client = Client.objects.filter(email__iexact=sender_email).first()

        if client:
            client.consent_marketing = consent_marketing
            if consent_marketing:
                client.consent_date = timezone.now()
            client.save(update_fields=["consent_marketing", "consent_date", "updated_at"])

        from ..services import notify_new_message

        notify_new_message(message)

        if self._is_htmx():
            return TemplateResponse(
                self.request,
                "features/conversations/partials/success_message.html",
            )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self._is_htmx():
            return TemplateResponse(
                self.request,
                "features/conversations/partials/form.html",
                {"form": form},
                status=422,
            )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sent"] = self.request.GET.get("sent") == "1"
        return context
