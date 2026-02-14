from typing import Any

from core.cache import get_cached_data

from ..models import StaticPageSeo


class SeoSelector:
    """
    Selector for retrieving SEO data for static pages.
    Uses Redis caching for performance.
    """

    @staticmethod
    def get_seo(page_key: str) -> Any:
        """
        Fetches SEO object by page key (e.g., 'home', 'contacts').
        """

        def fetch():
            try:
                return StaticPageSeo.objects.get(page_key=page_key)
            except StaticPageSeo.DoesNotExist:
                return None

        return get_cached_data(f"seo_cache_{page_key}", fetch)
