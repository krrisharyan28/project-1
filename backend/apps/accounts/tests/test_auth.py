"""Tests for registration, JWT login, and the /me endpoint."""
import pytest


@pytest.mark.django_db
def test_register_creates_user(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {"username": "newbie", "email": "n@example.com", "password": "strongpass1"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["username"] == "newbie"
    assert "password" not in resp.data


@pytest.mark.django_db
def test_register_rejects_short_password(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {"username": "x", "password": "short"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_login_returns_tokens(api_client, analyst):
    resp = api_client.post(
        "/api/auth/login/",
        {"username": "tester", "password": "pass12345"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data and "refresh" in resp.data


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    assert api_client.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_me_returns_profile(auth_client):
    resp = auth_client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.data["username"] == "tester"
    assert resp.data["role"] == "analyst"
