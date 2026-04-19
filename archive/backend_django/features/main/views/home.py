from core.logger import log
from django.views.generic import TemplateView

from ...system.selectors.seo import SeoSelector
from ..services.home_service import HomeService


class HomeView(TemplateView):
    template_name = "home/home.html"  # Correct path

    def get_context_data(self, **kwargs):
        log.debug("View: HomeView | Action: GetContext")
        context = super().get_context_data(**kwargs)

        # 1. Bento Grid Data (Categories grouped by bento_group)
        context["bento"] = HomeService.get_bento_context()

        # 2. SEO Data
        context["seo"] = SeoSelector.get_seo("home")

        log.info(f"View: HomeView | Action: Success | bento_groups={len(context['bento'])}")
        return context
