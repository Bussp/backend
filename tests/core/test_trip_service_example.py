from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.bus import RouteIdentifier
from src.core.models.user import User
from src.core.ports.trip_repository import TripRepository
from src.core.ports.user_repository import UserRepository
from src.core.services.trip_service import TripService

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def calculate_expected_score(distance: int) -> float:
    return round(distance * 0.077)


@pytest.mark.asyncio
async def test_create_trip_calculates_score_correctly() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Test User",
        email="test@example.com",
        score=0,
        password="hashed_password",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    distance = 1000

    trip = await service.create_trip(
        email="test@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=distance,
        trip_datetime=datetime(2025, 10, 16, 10, 0, 0),
    )

    expected_score = 77.0
    assert trip.score == expected_score
    assert trip.email == "test@example.com"
    assert trip.route.bus_line == "8000"

    user_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_awaited_once_with("test@example.com", expected_score)


@pytest.mark.asyncio
async def test_create_trip_fails_for_nonexistent_user(mocker: "MockerFixture") -> None:
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock()

    service = TripService(trip_repo, user_repo)

    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="ghost@example.com",
            route=RouteIdentifier(bus_line="8000", bus_direction=1),
            distance=1000,
            trip_datetime=datetime.now(),
        )

    user_repo.get_user_by_email.assert_awaited_once_with("ghost@example.com")
    trip_repo.save_trip.assert_not_awaited()
    user_repo.add_user_score.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiple_trips(mocker: "MockerFixture") -> None:
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Bob",
        email="bob@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    trip1 = await service.create_trip(
        email="bob@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=500,
        trip_datetime=datetime.now(),
    )

    trip2 = await service.create_trip(
        email="bob@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=2),
        distance=1500,
        trip_datetime=datetime.now(),
    )

    assert trip1.score == calculate_expected_score(trip1.distance)
    assert trip1.route.bus_line == "8000"
    assert trip2.score == calculate_expected_score(trip2.distance)
    assert trip2.route.bus_direction == 2
    assert trip_repo.save_trip.await_count == 2
    assert user_repo.add_user_score.await_count == 2
    user_repo.add_user_score.assert_any_await("bob@example.com", trip1.score)
    user_repo.add_user_score.assert_any_await("bob@example.com", trip2.score)


@pytest.mark.asyncio
async def test_handles_repository_save_error(mocker: "MockerFixture") -> None:
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Charlie",
        email="charlie@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock(side_effect=RuntimeError("Database connection lost!"))

    service = TripService(trip_repo, user_repo)

    with pytest.raises(RuntimeError, match="Database connection lost"):
        await service.create_trip(
            email="charlie@example.com",
            route=RouteIdentifier(bus_line="8000", bus_direction=1),
            distance=1000,
            trip_datetime=datetime.now(),
        )

    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_not_awaited()
