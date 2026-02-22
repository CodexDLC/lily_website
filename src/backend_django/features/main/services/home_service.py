from ..models import Category
from ..selectors.categories import CategorySelector


class HomeService:
    """
    Service layer for the Home Page.
    Prepares context data for templates.
    """

    @staticmethod
    def get_bento_context() -> list[Category]:
        """
        Fetches categories and groups them by 'bento_group' for the main page grid.
        Returns a list of Category objects, one for each group, with aggregated min_price.
        """
        categories = CategorySelector.get_for_home_bento()

        bento_map: dict[str, Category] = {}

        for cat in categories:
            group_key = cat.bento_group

            if group_key not in bento_map:
                bento_map[group_key] = cat
            else:
                # Aggregate min_price across all categories in the same group
                existing_cat = bento_map[group_key]
                if cat.min_price is not None and (
                    existing_cat.min_price is None or cat.min_price < existing_cat.min_price
                ):
                    existing_cat.min_price = cat.min_price

        # Return as a list to allow iteration in template
        return list(bento_map.values())
