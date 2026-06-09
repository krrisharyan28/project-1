"""Shared pytest fixtures for the backend test suite."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def analyst(db):
    return User.objects.create_user(
        username="tester",
        email="tester@example.com",
        password="pass12345",
        role=User.Role.ANALYST,
    )


@pytest.fixture
def auth_client(api_client, analyst):
    """An APIClient already authenticated as the analyst user."""
    api_client.force_authenticate(user=analyst)
    return api_client
