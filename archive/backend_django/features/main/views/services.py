from core.logger import log
from django.http import Http404
from django.views.generic import DetailView, TemplateView

from ...system.selectors.seo import SeoSelector
from ..models import Category
from ..selectors.categories import CategorySelector


class ServicesIndexView(TemplateView):
    """
    Displays the full list of services grouped by bento islands.
    Can be filtered by bento_group: /services/ or /services/?bento=nails
    """

    template_name = "services/services.html"

    def get_context_data(self, **kwargs):
        log.debug("View: ServicesIndexView | Action: GetContext")
        context = super().get_context_data(**kwargs)

        # Get bento_group filter from query params (optional)
        bento_filter = self.request.GET.get("bento", None)
        log.debug(f"View: ServicesIndexView | Action: Filtering | bento={bento_filter}")

        # Get islands (categories grouped by bento_group)
        context["islands"] = CategorySelector.get_for_price_list(bento_group=bento_filter)

        # SEO
        context["seo"] = SeoSelector.get_seo("services_index")

        # Filter info for template
        context["bento_filter"] = bento_filter

        log.info(f"View: ServicesIndexView | Action: Success | islands_count={len(context['islands'])}")
        return context


class ServiceDetailView(DetailView):
    """
    Displays a single category with its services grouped.
    Example: /services/nails/
    """

    model = Category
    template_name = "services/detail.html"  # Correct path
    context_object_name = "category"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        log.debug(f"View: ServiceDetailView | Action: GetObject | slug={slug}")

        category = CategorySelector.get_detail(slug)
        if not category:
            log.warning(f"View: ServiceDetailView | Action: NotFound | slug={slug}")
            raise Http404("Category not found")
        return category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch other active categories for bento cross-linking, excluding the current one
        current_category = self.get_object()
        all_categories = CategorySelector.get_for_home_bento()
        context["other_categories"] = [cat for cat in all_categories if cat.slug != current_category.slug]

        log.info(f"View: ServiceDetailView | Action: Success | slug={current_category.slug}")
        return context
