from ninja import NinjaAPI

# Removed urls_namespace to avoid ConfigError on double import
api = NinjaAPI(title="lily_website API", version="1.0.0")
