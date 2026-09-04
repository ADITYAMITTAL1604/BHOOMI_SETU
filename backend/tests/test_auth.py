"""Integration tests for Authentication, Token Refresh, Reuse Detection, and Logout."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


def test_login_success(client: TestClient, test_admin_user: User):
    """Test login with valid credentials returns access and refresh tokens."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, test_admin_user: User):
    """Test login with wrong password returns 401 without enumerating user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "WrongPassword!"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "non_existent_user_999", "password": "password123"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_refresh_and_reuse_detection(client: TestClient, test_admin_user: User):
    """Test token refresh and immediate revocation on token reuse attempt."""
    # 1. Login to get initial refresh token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "password123"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    tokens1 = login_res.json()
    old_refresh = tokens1["refresh_token"]

    # 2. Refresh token once (valid transition)
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_res.status_code == status.HTTP_200_OK
    tokens2 = refresh_res.json()
    new_refresh = tokens2["refresh_token"]
    assert new_refresh != old_refresh

    # 3. Attempt to reuse old_refresh token (simulating token theft/replay)
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_res.status_code == status.HTTP_401_UNAUTHORIZED

    # 4. Confirm family revocation: the new_refresh token must now also be revoked!
    subsequent_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert subsequent_res.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout(client: TestClient, test_admin_user: User):
    """Test logout revokes user sessions and returns success."""
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin", "password": "password123"},
    )
    token = login_res.json()["access_token"]
    refresh = login_res.json()["refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == status.HTTP_200_OK

    # Trying to refresh with the logged out session should fail
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert ref_res.status_code == status.HTTP_401_UNAUTHORIZED
