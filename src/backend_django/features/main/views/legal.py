from django.views.generic import TemplateView


class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"


class DatenschutzView(TemplateView):
    template_name = "legal/datenschutz.html"


class FaqView(TemplateView):
    template_name = "legal/faq.html"
