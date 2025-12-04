"""
Tests for UserController - API endpoints for user management.

These tests verify the HTTP layer using FastAPI's TestClient.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.core.models.user import User
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_user_service() -> MagicMock:
    """Create a mock UserService."""
    return MagicMock()


def test_create_user_success(client: TestClient, mock_user_service: MagicMock) -> None:
    """Test successful user registration."""

    mock_user = User(
        name="John Doe",
        email="john@example.com",
        password="hashed_password",
        score=0,
    )
    mock_user_service.create_user = AsyncMock(return_value=mock_user)

    from src.web.auth import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.post(
        "/users/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["score"] == 0
    assert "password" not in data


def test_create_user_already_exists(
    client: TestClient, mock_user_service: MagicMock
) -> None:
    """Test user registration fails when email already exists."""

    mock_user_service.create_user = AsyncMock(
        side_effect=ValueError("User with email john@example.com already exists")
    )

    from src.web.auth import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.post(
        "/users/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_login_user_success(client: TestClient, mock_user_service: MagicMock) -> None:
    """Test successful user login returns JWT token."""

    mock_user = User(
        name="Alice",
        email="alice@example.com",
        password="hashed_password",
        score=100,
    )
    mock_user_service.login_user = AsyncMock(return_value=mock_user)

    from src.web.auth import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.post(
        "/users/login",
        data={
            "username": "alice@example.com",
            "password": "mypassword",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)


def test_login_user_invalid_credentials(
    client: TestClient, mock_user_service: MagicMock
) -> None:
    """Test login fails with invalid credentials."""

    mock_user_service.login_user = AsyncMock(return_value=None)

    from src.web.auth import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.post(
        "/users/login",
        data={
            "username": "alice@example.com",
            "password": "wrongpassword",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password"

def test_get_current_user_info_success(
    client: TestClient, mock_user_service: MagicMock
) -> None:
    """Test accessing /me endpoint with valid JWT token."""

    mock_user = User(
        name="Charlie",
        email="charlie@example.com",
        password="hashed_password",
        score=75,
    )
    mock_user_service.get_user = AsyncMock(return_value=mock_user)

    from src.web.auth import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    with patch(
        "src.web.auth.verify_token",
        return_value={"sub": "charlie@example.com"},
    ):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer valid_token_here"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Charlie"
    assert data["email"] == "charlie@example.com"
    assert data["score"] == 75


def test_get_current_user_info_no_token(client: TestClient) -> None:
    """Test accessing /me endpoint without token returns 401."""

    response = client.get("/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_info_invalid_token(
    client: TestClient, mock_user_service: MagicMock
) -> None:
    """Test accessing /me endpoint with invalid token returns 401."""

    with (
        patch("src.web.auth.get_user_service", return_value=mock_user_service),
        patch("src.web.auth.verify_token", return_value=None),
    ):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"


def test_create_user_validation_error(client: TestClient) -> None:
    """Test user registration with invalid data returns 422."""

    response = client.post(
        "/users/register",
        json={
            "name": "John Doe",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_user_missing_credentials(client: TestClient) -> None:
    """Test login with missing credentials returns 422."""

    response = client.post(
        "/users/login",
        data={
            "username": "alice@example.com",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
