from .services.notification_service import PromoService


def active_promo(request):
    """
    Context processor to add the current active promo to all templates.
    """
    # We can get the page slug from the request path to filter promos by page
    path = request.path.strip("/").split("/")
    page_slug = path[0] if path and path[0] else "home"

    return {"active_promo": PromoService.get_active_promo(page_slug=page_slug)}
