"""
Pytest configuration and shared fixtures for core app tests.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.trainers.factories import OrganizationFactory, TrainerFactory
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


@pytest.fixture
def test_organization():
    """Create a test organization for use across tests."""
    return OrganizationFactory(
        name="Test Fitness Center",
        code="TEST001"
    )


@pytest.fixture
def test_trainer_user(test_organization):
    """Create a trainer user with profile."""
    user = UserFactory(
        username="test_trainer",
        email="trainer@test.com"
    )
    TrainerFactory(
        user=user,
        organization=test_organization,
        phone="010-1234-5678"
    )
    return user


@pytest.fixture
def test_superuser():
    """Create a superuser for permission tests."""
    return UserFactory(
        username="admin",
        email="admin@test.com",
        is_superuser=True,
        is_staff=True
    )


@pytest.fixture
def test_client(test_trainer_user):
    """Create a test client."""
    return ClientFactory(
        trainer=test_trainer_user,
        name="테스트 고객",
        gender="M",
        age=30,
        height=175,
        weight=70,
        email="client@test.com",
        phone="010-9876-5432"
    )


@pytest.fixture
def another_organization():
    """Create another organization for cross-org tests."""
    return OrganizationFactory(
        name="Another Fitness Center",
        code="OTHER001"
    )


@pytest.fixture
def another_trainer_user(another_organization):
    """Create a trainer from another organization."""
    user = UserFactory(
        username="another_trainer",
        email="another@test.com"
    )
    TrainerFactory(
        user=user,
        organization=another_organization
    )
    return user


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This eliminates the need for @pytest.mark.django_db on every test.
    """
    pass