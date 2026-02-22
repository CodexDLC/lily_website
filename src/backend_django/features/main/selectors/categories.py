from core.cache import get_cached_data
from django.db.models import Count, Min, Prefetch, Q
from features.booking.models import Master

from ..models import Category, Service


class CategorySelector:
    """
    Selector for retrieving Category data.
    Optimized for different use cases (Home Bento, Price List, Detail).
    Uses Redis caching for performance.
    """

    @staticmethod
    def get_bento_groups():
        """
        Returns categories grouped by bento_group for displaying bento cards on home page.
        """

        def fetch():
            categories = (
                Category.objects.filter(is_active=True)
                .only("title", "slug", "image", "bento_group", "is_planned", "description", "order")
                .order_by("order")
            )
            bento_map = {}
            for cat in categories:
                bento_map[cat.bento_group] = cat
            return bento_map

        return get_cached_data("bento_groups_cache", fetch)

    @staticmethod
    def get_for_home_bento():
        """
        Returns active categories for the Home Page Bento Grid.
        Includes active_masters_count to determine 'Coming Soon' status.
        Annotates with min_price from active services, excluding add-ons.
        """

        def fetch():
            return list(
                Category.objects.filter(is_active=True)
                .annotate(
                    active_masters_count=Count("masters", filter=Q(masters__status=Master.STATUS_ACTIVE)),
                    min_price=Min("services__price", filter=Q(services__is_active=True, services__is_addon=False)),
                )
                .only("title", "slug", "image", "bento_group", "is_planned", "description")
                .order_by("order")
            )

        # Changed cache key to v5 to force refresh after is_addon field was added and populated
        return get_cached_data("home_bento_cache_v5", fetch)

    @staticmethod
    def get_for_price_list(bento_group=None):
        """
        Returns list of categories with their services.
        """

        def fetch():
            services_prefetch = Prefetch(
                "services",
                queryset=Service.objects.filter(is_active=True).order_by("order", "title"),
            )
            queryset = Category.objects.filter(is_active=True).prefetch_related(services_prefetch).order_by("order")
            if bento_group:
                queryset = queryset.filter(bento_group=bento_group)
            return list(queryset)

        key = f"price_list_cache_{bento_group}" if bento_group else "price_list_cache_all"
        return get_cached_data(key, fetch)

    @staticmethod
    def get_detail(slug: str):
        """
        Returns a single category with all its services and masters.
        """

        def fetch():
            try:
                services_prefetch = Prefetch(
                    "services",
                    queryset=Service.objects.filter(is_active=True).order_by("order", "title"),
                )
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

        return get_cached_data(f"category_detail_cache_{slug}", fetch)
