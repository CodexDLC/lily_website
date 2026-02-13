from typing import Any

from ..models import Category
from ..selectors.categories import CategorySelector


class HomeService:
    """
    Service layer for the Home Page.
    Prepares context data for templates.
    """

    @staticmethod
    def get_bento_context() -> dict[str, Any]:
        """
        Fetches categories and groups them by 'bento_group' for the main page grid.

        Returns:
            Dict[str, Category]: A dictionary where keys are bento_group slugs
                                 ('hair', 'nails', etc.) and values are Category objects.
                                 If multiple categories share a group, the first one (by order) is taken.
        """
        categories = CategorySelector.get_for_home_bento()

        bento_data: dict[str, Any] = {}

        # Define expected groups to ensure keys exist even if empty
        expected_groups = [g[0] for g in Category.BENTO_GROUPS]
        for group in expected_groups:
            bento_data[group] = None

        for cat in categories:
            group_key = cat.bento_group

            # Logic: If multiple categories have the same group, take the first one (by order)
            if bento_data.get(group_key) is None:
                bento_data[group_key] = cat

        return bento_data
