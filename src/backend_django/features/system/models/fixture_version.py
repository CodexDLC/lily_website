from django.db import models


class FixtureVersion(models.Model):
    name = models.CharField(max_length=100, unique=True)
    content_hash = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
