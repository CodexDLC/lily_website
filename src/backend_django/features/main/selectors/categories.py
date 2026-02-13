from django.db.models import Prefetch
from features.booking.models import Master

from ..models import Category, Service


class CategorySelector:
    """
    Selector for retrieving Category data.
    Optimized for different use cases (Home Bento, Price List, Detail).
    """

    @staticmethod
    def get_bento_groups():
        """
        Returns categories grouped by bento_group for displaying bento cards on home page.
        Returns dict: {bento_group: Category}
        Assumes one category per bento_group (after refactoring).
        """
        categories = (
            Category.objects.filter(is_active=True)
            .only("title", "slug", "image", "bento_group", "is_planned", "description", "order")
            .order_by("order")
        )

        # Map by bento_group
        bento_map = {}
        for cat in categories:
            bento_map[cat.bento_group] = cat

        return bento_map

    @staticmethod
    def get_for_home_bento():
        """
        Returns active categories for the Home Page Bento Grid.
        """
        categories = (
            Category.objects.filter(is_active=True)
            .only("title", "slug", "image", "bento_group", "is_planned", "description")
            .order_by("order")
        )

        return categories

    @staticmethod
    def get_for_price_list(bento_group=None):
        """
        Returns list of categories with their services.
        """
        # Prefetch services
        services_prefetch = Prefetch(
            "services",
            queryset=Service.objects.filter(is_active=True).order_by("order", "title"),
        )

        # Get categories
        queryset = Category.objects.filter(is_active=True).prefetch_related(services_prefetch).order_by("order")

        if bento_group:
            queryset = queryset.filter(bento_group=bento_group)

        return queryset

    @staticmethod
    def get_detail(slug: str):
        """
        Returns a single category with all its services and masters.
        Used for /services/<slug>/ page.
        """
        try:
            # Prefetch services
            services_prefetch = Prefetch(
                "services",
                queryset=Service.objects.filter(is_active=True).order_by("order", "title"),
            )

            # Prefetch masters (only active)
            masters_prefetch = Prefetch(
                "masters",
                queryset=Master.objects.filter(status="active").order_by("order", "name"),
            )

            return (
                Category.objects.filter(is_active=True)
                .prefetch_related(services_prefetch, masters_prefetch)
                .get(slug=slug)
            )

        except Category.DoesNotExist:
            return None
