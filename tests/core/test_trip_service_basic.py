"""Basic unit tests for TripService.

Two tests:
- when user repository returns None -> create_trip raises ValueError
- when user repository returns a user -> create_trip returns a Trip and updates score
"""

from datetime import datetime
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.trip import Trip
from src.core.models.user import User
from src.core.ports.trip_repository import TripRepository
from src.core.ports.user_repository import UserRepository
from src.core.services.trip_service import TripService


@pytest.mark.asyncio
async def test_create_trip_no_user() -> None:
    """If user isn't found, create_trip should raise ValueError and not save a trip."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)
    trip_repo.save_trip = AsyncMock()
    user_repo.add_user_score = AsyncMock()

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act / Assert
    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="missing@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )

    user_repo.get_user_by_email.assert_awaited_once_with("missing@example.com")
    trip_repo.save_trip.assert_not_awaited()  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_trip_single_user() -> None:
    """When a user exists, create_trip should save the trip, return it, and update user's score."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Test", email="user@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    distance = 1500  # metros
    expected_score = (distance // 1000) * 77  # 77 pontos por km inteiro

    # Act
    trip = await service.create_trip(
        email="user@example.com",
        bus_line="9000",
        bus_direction=2,
        distance=distance,
        trip_date=datetime(2025, 11, 15, 12, 0, 0),
    )

    # Assert
    assert isinstance(trip, Trip)
    assert trip.score == expected_score
    assert trip.email == "user@example.com"

    user_repo.get_user_by_email.assert_awaited_once_with("user@example.com")
    trip_repo.save_trip.assert_awaited_once()  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_awaited_once_with("user@example.com", expected_score)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_trip_zero_distance() -> None:
    """Distance zero should produce score 0 and still save the trip."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Zero", email="zero@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act
    trip = await service.create_trip(
        email="zero@example.com",
        bus_line="0000",
        bus_direction=1,
        distance=0,
        trip_date=datetime(2025, 11, 15, 12, 0, 0),
    )

    # Assert
    assert isinstance(trip, Trip)
    assert trip.score == 0
    user_repo.add_user_score.assert_awaited_once_with("zero@example.com", 0)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_trip_negative_distance() -> None:
    """Negative distance should be rejected by the service (failure response).

    We expect the service to validate distance and raise ValueError for negative values.
    """
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Neg", email="neg@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock()

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act & Assert
    with pytest.raises(ValueError, match="distance"):
        await service.create_trip(
            email="neg@example.com",
            bus_line="-100",
            bus_direction=1,
            distance=-150,
            trip_date=datetime(2025, 11, 15, 12, 0, 0),
        )

    # Ensure repository save/add were not called
    trip_repo.save_trip.assert_not_awaited()  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_trip_very_large_distance() -> None:
    """Very large distance should produce a large score without overflow/error."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Big", email="big@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    big_distance = 10_000_000  # 10 million meters

    # Act
    trip = await service.create_trip(
        email="big@example.com",
        bus_line="BIG",
        bus_direction=2,
        distance=big_distance,
        trip_date=datetime(2025, 11, 15, 12, 0, 0),
    )

    # Assert
    expected_score = (big_distance // 1000) * 77  # 77 pontos por km inteiro
    assert trip.score == expected_score
    user_repo.add_user_score.assert_awaited_once_with("big@example.com", expected_score)  # type: ignore[attr-defined]
