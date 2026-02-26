from core.logger import log
from django.views.generic import TemplateView
from features.booking.selectors.masters import MasterSelector
from features.system.models.site_settings import SiteSettings
from features.system.selectors.seo import SeoSelector


class TeamView(TemplateView):
    template_name = "team/team.html"

    def get_context_data(self, **kwargs):
        log.debug("View: TeamView | Action: GetContext")
        context = super().get_context_data(**kwargs)

        # Masters
        context["owner"] = MasterSelector.get_owner()
        context["team"] = MasterSelector.get_team_members()

        # Settings (for hiring block)
        context["settings"] = SiteSettings.load()

        # SEO
        context["seo"] = SeoSelector.get_seo("team")

        log.info(f"View: TeamView | Action: Success | team_count={len(context['team'])}")
        return context
