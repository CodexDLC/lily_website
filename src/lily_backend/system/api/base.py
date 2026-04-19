from ninja import NinjaAPI

api = NinjaAPI(title="Lily API", version="2.0")


@api.get("/v1/health", tags=["System"])
def health_check(request):
    """Simple health check endpoint."""
    return {"status": "ok"}
