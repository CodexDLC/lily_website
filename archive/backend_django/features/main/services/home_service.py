from core.logger import log

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
        log.debug("Service: HomeService | Action: GetBentoContext")

        categories = CategorySelector.get_for_home_bento()
        log.debug(f"Service: HomeService | Action: FetchCategories | count={len(categories)}")

        bento_map: dict[str, Category] = {}

        for cat in categories:
            group_key = cat.bento_group

            if group_key not in bento_map:
                bento_map[group_key] = cat
                log.debug(f"Service: HomeService | Action: GroupCategory | group={group_key} | category={cat.slug}")
            else:
                # Aggregate min_price across all categories in the same group
                existing_cat = bento_map[group_key]
                if cat.min_price is not None and (
                    existing_cat.min_price is None or cat.min_price < existing_cat.min_price
                ):
                    log.debug(
                        f"Service: HomeService | Action: UpdateMinPrice | group={group_key} | from={existing_cat.min_price} | to={cat.min_price}"
                    )
                    existing_cat.min_price = cat.min_price

        result = list(bento_map.values())
        log.info(f"Service: HomeService | Action: Success | groups_count={len(result)}")

        # Return as a list to allow iteration in template
        return result
