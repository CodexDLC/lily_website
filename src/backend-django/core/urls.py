"""
lily_website — URL Configuration.

Features auto-included via include().
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("features.main.urls")),
]
