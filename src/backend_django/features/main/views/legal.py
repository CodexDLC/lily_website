from core.logger import log
from django.shortcuts import render
from django.views.generic import TemplateView


class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"

    def get_context_data(self, **kwargs):
        log.debug("View: ImpressumView | Action: GetContext")
        return super().get_context_data(**kwargs)


class DatenschutzView(TemplateView):
    template_name = "legal/datenschutz.html"

    def get_context_data(self, **kwargs):
        log.debug("View: DatenschutzView | Action: GetContext")
        return super().get_context_data(**kwargs)


class FaqView(TemplateView):
    template_name = "legal/faq.html"

    def get_context_data(self, **kwargs):
        log.debug("View: FaqView | Action: GetContext")
        return super().get_context_data(**kwargs)


class BuchungsregelnView(TemplateView):
    template_name = "legal/buchungsregeln.html"

    def get_context_data(self, **kwargs):
        log.debug("View: BuchungsregelnView | Action: GetContext")
        return super().get_context_data(**kwargs)


def ratelimit_view(request, exception):
    """View called when ratelimit is exceeded."""
    log.warning(f"View: RateLimit | Action: Blocked | ip={request.META.get('REMOTE_ADDR')} | path={request.path}")
    return render(request, "errors/429.html", status=429)
