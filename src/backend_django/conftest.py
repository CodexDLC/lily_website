"""
Pytest configuration for Django tests.

Configures test database, Redis, and other fixtures.
"""

import os

import pytest

# Prevent NinjaAPI from raising ConfigError during tests due to multiple imports
os.environ["NINJA_SKIP_REGISTRY"] = "True"


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This prevents the need to mark every test with @pytest.mark.django_db.
    """
    pass
