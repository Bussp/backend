"""
Tests for UserService - Business logic for user management.

These tests verify the user service layer in isolation using mocked dependencies.
"""

from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.user import User
from src.core.ports.password_hasher import PasswordHasherPort
from src.core.ports.user_repository import UserRepository
from src.core.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_user_success() -> None:
    """Test successful user creation with password hashing."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)
    password_hasher.hash = lambda pwd: f"hashed_{pwd}"

    created_user = User(
        name="John Doe",
        email="john@example.com",
        password="hashed_securepass123",
        score=0,
    )
    user_repo.save_user = AsyncMock(return_value=created_user)

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.create_user(
        name="John Doe",
        email="john@example.com",
        password="securepass123",
    )

    assert result.name == "John Doe"
    assert result.email == "john@example.com"
    assert result.password == "hashed_securepass123"
    assert result.score == 0
    user_repo.get_user_by_email.assert_called_once_with("john@example.com")
    user_repo.save_user.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_already_exists() -> None:
    """Test user creation fails when email already exists."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    existing_user = User(
        name="Existing User",
        email="john@example.com",
        password="hashed_password",
        score=10,
    )
    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="User with email john@example.com already exists"):
        await service.create_user(
            name="John Doe",
            email="john@example.com",
            password="securepass123",
        )

    user_repo.get_user_by_email.assert_called_once_with("john@example.com")
    user_repo.save_user.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_found() -> None:
    """Test retrieving an existing user by email."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    expected_user = User(
        name="Jane Doe",
        email="jane@example.com",
        password="hashed_password",
        score=50,
    )
    user_repo.get_user_by_email = AsyncMock(return_value=expected_user)

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.get_user("jane@example.com")

    assert result is not None
    assert result.name == "Jane Doe"
    assert result.email == "jane@example.com"
    assert result.score == 50
    user_repo.get_user_by_email.assert_called_once_with("jane@example.com")


@pytest.mark.asyncio
async def test_get_user_not_found() -> None:
    """Test retrieving a non-existent user returns None."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.get_user("nonexistent@example.com")

    assert result is None
    user_repo.get_user_by_email.assert_called_once_with("nonexistent@example.com")


@pytest.mark.asyncio
async def test_login_user_success() -> None:
    """Test successful user login with correct credentials."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    stored_user = User(
        name="Alice",
        email="alice@example.com",
        password="hashed_mypassword",
        score=100,
    )
    user_repo.get_user_by_email = AsyncMock(return_value=stored_user)
    password_hasher.verify = (
        lambda plain, hashed: plain == "mypassword" and hashed == "hashed_mypassword"
    )

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.login_user("alice@example.com", "mypassword")

    assert result is not None
    assert result.email == "alice@example.com"
    assert result.name == "Alice"
    user_repo.get_user_by_email.assert_called_once_with("alice@example.com")


@pytest.mark.asyncio
async def test_login_user_wrong_password() -> None:
    """Test login fails with incorrect password."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    stored_user = User(
        name="Bob",
        email="bob@example.com",
        password="hashed_correctpassword",
        score=50,
    )
    user_repo.get_user_by_email = AsyncMock(return_value=stored_user)
    password_hasher.verify = (
        lambda plain, hashed: plain == "correctpassword" and hashed == "hashed_correctpassword"
    )

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.login_user("bob@example.com", "wrongpassword")

    assert result is None
    user_repo.get_user_by_email.assert_called_once_with("bob@example.com")


@pytest.mark.asyncio
async def test_login_user_not_found() -> None:
    """Test login fails when user doesn't exist."""

    user_repo = create_autospec(UserRepository, instance=True)
    password_hasher = create_autospec(PasswordHasherPort, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)

    service = UserService(user_repo, password_hasher)  # type: ignore[arg-type]

    result = await service.login_user("nonexistent@example.com", "anypassword")

    assert result is None
    user_repo.get_user_by_email.assert_called_once_with("nonexistent@example.com")
