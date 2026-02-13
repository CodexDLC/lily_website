from typing import Any

from ..models import StaticPageSeo


class SeoSelector:
    """
    Selector for retrieving SEO data for static pages.
    """

    @staticmethod
    def get_seo(page_key: str) -> Any:
        """
        Fetches SEO object by page key (e.g., 'home', 'contacts').
        Returns None if not found (template should handle fallback).
        """
        try:
            return StaticPageSeo.objects.get(page_key=page_key)
        except StaticPageSeo.DoesNotExist:
            return None
