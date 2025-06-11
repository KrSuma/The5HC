"""
Global pytest configuration for The5HC Django project.
This file contains fixtures and settings that are available to all tests.
"""
import pytest
from django.test import Client
from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Load fixtures for the entire test session.
    This runs once per test session.
    """
    with django_db_blocker.unblock():
        # Load any initial data if needed
        pass


@pytest.fixture
def user_factory(django_user_model):
    """
    Factory for creating test users.
    Will be replaced by proper factory_boy factories.
    """
    def create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'is_active': True,
        }
        defaults.update(kwargs)
        password = defaults.pop('password')
        user = django_user_model.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user
    return create_user


@pytest.fixture
def authenticated_client(client, user_factory):
    """
    Client with an authenticated user.
    """
    user = user_factory()
    client.force_login(user)
    return client, user


@pytest.fixture
def admin_user(user_factory):
    """
    Create an admin/superuser for testing.
    """
    return user_factory(
        username='admin',
        email='admin@example.com',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """
    Client with an authenticated admin user.
    """
    client.force_login(admin_user)
    return client, admin_user


# Database markers for easy test categorization
pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Grant database access to all tests by default.
    Individual tests can override with @pytest.mark.django_db(transaction=True) if needed.
    """
    pass


@pytest.fixture
def api_client():
    """
    DRF API test client (for future API testing).
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def settings_override(settings):
    """
    Helper fixture for test-specific settings overrides.
    """
    def override(**kwargs):
        for key, value in kwargs.items():
            setattr(settings, key, value)
    return override


# Disable logging during tests for cleaner output
@pytest.fixture(autouse=True)
def disable_logging(caplog):
    """
    Disable logging during tests unless explicitly needed.
    """
    import logging
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)