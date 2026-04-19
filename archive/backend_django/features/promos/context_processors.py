from .services.notification_service import PromoService

_EXCLUDED_PROMO_PAGES = {"impressum", "datenschutz", "faq", "buchungsregeln"}


def active_promo(request):
    """
    Context processor to add the current active promo to all templates.
    """
    path = request.path.strip("/").split("/")
    page_slug = path[0] if path and path[0] else "home"

    if page_slug in _EXCLUDED_PROMO_PAGES:
        return {"active_promo": None}

    return {"active_promo": PromoService.get_active_promo(page_slug=page_slug)}
