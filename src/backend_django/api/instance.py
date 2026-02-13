from ninja import NinjaAPI

# Using a specific urls_namespace to help Ninja distinguish the API instance.
# This often resolves ConfigError during Django's double-import cycles (like autoreload).
api = NinjaAPI(title="lily_website API", version="1.0.0", urls_namespace="api_v1")
