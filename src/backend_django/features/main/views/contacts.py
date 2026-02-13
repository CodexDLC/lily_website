from django.shortcuts import render
from django.views.generic import FormView
from features.system.models.site_settings import SiteSettings
from features.system.selectors.seo import SeoSelector

from ..forms import ContactForm
from ..services.contact_service import ContactService


class ContactsView(FormView):
    template_name = "contacts/contacts.html"
    form_class = ContactForm
    success_url = "/contacts/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ensure form is in context
        if "form" not in context:
            context["form"] = self.get_form()

        context["settings"] = SiteSettings.load()
        context["seo"] = SeoSelector.get_seo("contacts")
        return context

    def form_valid(self, form):
        # Create request via Service
        ContactService.create_request(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            contact_type=form.cleaned_data["contact_type"],
            contact_value=form.cleaned_data["contact_value"],
            message=form.cleaned_data["message"],
            topic=form.cleaned_data["topic"],
            consent_marketing=form.cleaned_data["consent_marketing"],
        )

        # HTMX Response
        if self.request.headers.get("HX-Request"):
            return render(self.request, "contacts/partials/success_message.html")

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request"):
            return render(self.request, "contacts/partials/form.html", {"form": form})
        return super().form_invalid(form)
