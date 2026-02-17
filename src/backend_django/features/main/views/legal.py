from django.shortcuts import render
from django.views.generic import TemplateView


class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"


class DatenschutzView(TemplateView):
    template_name = "legal/datenschutz.html"


class FaqView(TemplateView):
    template_name = "legal/faq.html"


def ratelimit_view(request, exception):
    """View called when ratelimit is exceeded."""
    return render(request, "errors/429.html", status=429)
