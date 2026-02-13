from django.conf import settings


def site_base_url(request):
    return {"SITE_BASE_URL": settings.SITE_BASE_URL}
