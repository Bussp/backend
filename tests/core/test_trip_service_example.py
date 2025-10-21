"""
Examples demonstrating intelligent mocking with autospec and pytest-mock.

Uses create_autospec() to create type-safe mocks that match port interfaces,
avoiding manual mock classes and reducing boilerplate.
"""

import pytest
from datetime import datetime
from unittest.mock import create_autospec

from src.core.models.user import User
from src.core.ports.user_repository import UserRepository
from src.core.ports.trip_repository import TripRepository
from src.core.services.trip_service import TripService


@pytest.mark.asyncio
async def test_create_trip_calculates_score_correctly():
    """Test score calculation with autospecced mocks."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Test User",
        email="test@example.com",
        score=0,
        password="hashed_password",
    )
    user_repo.get_user_by_email.return_value = test_user
    trip_repo.save_trip.side_effect = lambda t: t

    service = TripService(trip_repo, user_repo)

    # Act
    trip = await service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        trip_date=datetime(2025, 10, 16, 10, 0, 0),
    )

    # Assert
    assert trip.score == 10
    assert trip.email == "test@example.com"
    assert trip.bus_line == "8000"

    user_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_awaited_once_with("test@example.com", 10)


@pytest.mark.asyncio
async def test_create_trip_with_pytest_mock(mocker):
    """Test using pytest-mock fixture for cleaner syntax."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Alice",
        email="alice@example.com",
        score=0,
        password="secure_hash",
    )
    user_repo.get_user_by_email.return_value = test_user
    trip_repo.save_trip.side_effect = lambda t: t

    service = TripService(trip_repo, user_repo)

    # Act
    trip = await service.create_trip(
        email="alice@example.com",
        bus_line="9000",
        bus_direction=2,
        distance=2500,
        trip_date=datetime(2025, 10, 16, 14, 30, 0),
    )

    # Assert
    assert trip.score == 25
    user_repo.add_user_score.assert_awaited_once_with("alice@example.com", 25)


@pytest.mark.asyncio
async def test_create_trip_fails_for_nonexistent_user(mocker):
    """Test error handling when user doesn't exist."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    user_repo.get_user_by_email.return_value = None
    service = TripService(trip_repo, user_repo)

    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="ghost@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )

    user_repo.get_user_by_email.assert_awaited_once_with("ghost@example.com")
    trip_repo.save_trip.assert_not_awaited()
    user_repo.add_user_score.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiple_trips(mocker):
    """Test multiple sequential calls to the service."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Bob",
        email="bob@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email.return_value = test_user
    trip_repo.save_trip.side_effect = lambda t: t

    service = TripService(trip_repo, user_repo)

    # Act
    trip1 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=500,
        trip_date=datetime.now(),
    )

    trip2 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=2,
        distance=1500,
        trip_date=datetime.now(),
    )

    # Assert
    assert trip1.score == 5
    assert trip2.score == 15
    assert trip_repo.save_trip.await_count == 2
    assert user_repo.add_user_score.await_count == 2
    user_repo.add_user_score.assert_any_await("bob@example.com", 5)
    user_repo.add_user_score.assert_any_await("bob@example.com", 15)


@pytest.mark.asyncio
async def test_handles_repository_save_error(mocker):
    """Test error handling when repository fails."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Charlie",
        email="charlie@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email.return_value = test_user
    trip_repo.save_trip.side_effect = RuntimeError("Database connection lost!")

    service = TripService(trip_repo, user_repo)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Database connection lost"):
        await service.create_trip(
            email="charlie@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )

    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_not_awaited()
