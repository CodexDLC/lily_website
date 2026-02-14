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
        context = super().get_context_data(**kwargs)

        # Get bento_group filter from query params (optional)
        bento_filter = self.request.GET.get("bento", None)

        # Get islands (categories grouped by bento_group)
        context["islands"] = CategorySelector.get_for_price_list(bento_group=bento_filter)

        # SEO
        context["seo"] = SeoSelector.get_seo("services_index")

        # Filter info for template
        context["bento_filter"] = bento_filter

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
        category = CategorySelector.get_detail(slug)
        if not category:
            raise Http404("Category not found")
        return category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
