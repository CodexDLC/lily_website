from collections import defaultdict

from django.db.models import Prefetch

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
        Returns dict: {bento_group: [categories]}
        """
        categories = (
            Category.objects.filter(is_active=True)
            .only("title", "slug", "image", "bento_group", "is_planned", "description", "order")
            .order_by("order")
        )

        # Group by bento_group
        grouped = defaultdict(list)
        for cat in categories:
            grouped[cat.bento_group].append(cat)

        return dict(grouped)

    @staticmethod
    def get_for_home_bento():
        """
        Returns active categories for the Home Page Bento Grid.
        Optimized: fetches only fields needed for display (title, slug, image, bento_group, is_planned).
        """
        # Use filter(is_active=True) instead of .active() to avoid conflicts with MultilingualManager
        categories = (
            Category.objects.filter(is_active=True)
            .only("title", "slug", "image", "bento_group", "is_planned", "description")
            .order_by("order")
        )

        return categories

    @staticmethod
    def get_for_price_list(bento_group=None):
        """
        Returns categories grouped by bento_group with their services.
        Used for /services/ page (all islands) or /services/{bento}/ (filtered).

        Returns list structure:
        [
            {
                'bento_key': 'hair',
                'bento_title': 'Friseur & Styling',
                'categories': [
                    {
                        'category': Category object,
                        'services': [Service, Service, ...]
                    },
                    ...
                ]
            },
            ...
        ]
        """
        # Prefetch services with their groups
        services_prefetch = Prefetch(
            "services",
            queryset=Service.objects.filter(is_active=True).select_related("group").order_by("group__order", "order"),
        )

        # Get categories
        queryset = (
            Category.objects.filter(is_active=True).prefetch_related(services_prefetch, "groups").order_by("order")
        )

        # Filter by bento_group if provided
        if bento_group:
            queryset = queryset.filter(bento_group=bento_group)

        # Group by bento_group
        grouped = defaultdict(list)
        for category in queryset:
            grouped[category.bento_group].append(
                {
                    "category": category,
                    "services": category.services.all(),
                }
            )

        # Convert to list with bento titles
        islands = []
        for bento_key, categories in grouped.items():
            # Get display name for bento_group
            bento_title = dict(Category.BENTO_GROUPS).get(bento_key, bento_key)

            islands.append(
                {
                    "bento_key": bento_key,
                    "bento_title": bento_title,
                    "categories": categories,
                }
            )

        return islands

    @staticmethod
    def get_detail(slug: str):
        """
        Returns a single category with all its services and groups.
        Used for /services/<slug>/ page.
        """
        try:
            # Prefetch services and groups
            services_prefetch = Prefetch(
                "services",
                queryset=Service.objects.filter(is_active=True)
                .select_related("group")
                .order_by("group__order", "order"),
            )

            return (
                Category.objects.filter(is_active=True)
                .prefetch_related(
                    services_prefetch,
                    "groups",  # If we need to display groups separately
                )
                .get(slug=slug)
            )

        except Category.DoesNotExist:
            return None
