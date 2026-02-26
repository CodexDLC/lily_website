from typing import Any

from core.cache import get_cached_data
from core.logger import log

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
        log.debug(f"Selector: SeoSelector | Action: GetSeo | page_key={page_key}")

        def fetch():
            log.debug(f"Selector: SeoSelector | Action: FetchDB | page_key={page_key}")
            try:
                return StaticPageSeo.objects.get(page_key=page_key)
            except StaticPageSeo.DoesNotExist:
                log.warning(f"Selector: SeoSelector | Action: NotFound | page_key={page_key}")
                return None

        return get_cached_data(f"seo_cache_{page_key}", fetch)
