from datetime import datetime
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.bus import RouteIdentifier
from src.core.models.trip import Trip
from src.core.models.user import User
from src.core.ports.trip_repository import TripRepository
from src.core.ports.user_repository import UserRepository
from src.core.services.trip_service import TripService


@pytest.mark.asyncio
async def test_create_trip_no_user() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)
    trip_repo.save_trip = AsyncMock()
    user_repo.add_user_score = AsyncMock()

    service = TripService(trip_repo, user_repo)

    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="missing@example.com",
            route=RouteIdentifier(bus_line="8000", bus_direction=1),
            distance=1000,
            trip_datetime=datetime.now(),
        )

    user_repo.get_user_by_email.assert_awaited_once_with("missing@example.com")
    trip_repo.save_trip.assert_not_awaited()
    user_repo.add_user_score.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_trip_single_user() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Test", email="user@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    distance = 1500
    expected_score = (distance // 1000) * 77

    trip = await service.create_trip(
        email="user@example.com",
        route=RouteIdentifier(bus_line="9000", bus_direction=2),
        distance=distance,
        trip_datetime=datetime(2025, 11, 15, 12, 0, 0),
    )

    assert isinstance(trip, Trip)
    assert trip.score == expected_score
    assert trip.email == "user@example.com"
    assert trip.route.bus_line == "9000"

    user_repo.get_user_by_email.assert_awaited_once_with("user@example.com")
    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_awaited_once_with("user@example.com", expected_score)


@pytest.mark.asyncio
async def test_create_trip_zero_distance() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Zero", email="zero@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    trip = await service.create_trip(
        email="zero@example.com",
        route=RouteIdentifier(bus_line="0000", bus_direction=1),
        distance=0,
        trip_datetime=datetime(2025, 11, 15, 12, 0, 0),
    )

    assert isinstance(trip, Trip)
    assert trip.score == 0
    assert trip.route.bus_line == "0000"
    user_repo.add_user_score.assert_awaited_once_with("zero@example.com", 0)


@pytest.mark.asyncio
async def test_create_trip_negative_distance() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Neg", email="neg@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock()

    service = TripService(trip_repo, user_repo)

    with pytest.raises(ValueError, match="distance"):
        await service.create_trip(
            email="neg@example.com",
            route=RouteIdentifier(bus_line="-100", bus_direction=1),
            distance=-150,
            trip_datetime=datetime(2025, 11, 15, 12, 0, 0),
        )

    trip_repo.save_trip.assert_not_awaited()
    user_repo.add_user_score.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_trip_very_large_distance() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Big", email="big@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    big_distance = 10_000_000

    trip = await service.create_trip(
        email="big@example.com",
        route=RouteIdentifier(bus_line="BIG", bus_direction=2),
        distance=big_distance,
        trip_datetime=datetime(2025, 11, 15, 12, 0, 0),
    )

    expected_score = (big_distance // 1000) * 77
    assert trip.score == expected_score
    assert trip.route.bus_line == "BIG"
    user_repo.add_user_score.assert_awaited_once_with("big@example.com", expected_score)


@pytest.mark.asyncio
async def test_create_trip_stores_route_identifier() -> None:
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(name="Test", email="test@example.com", score=0, password="hash")
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)

    saved_trip = None

    async def capture_trip(t: Trip) -> Trip:
        nonlocal saved_trip
        saved_trip = t
        return t

    trip_repo.save_trip = AsyncMock(side_effect=capture_trip)

    service = TripService(trip_repo, user_repo)

    await service.create_trip(
        email="test@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=5000,
        trip_datetime=datetime(2025, 11, 15, 12, 0, 0),
    )

    assert saved_trip is not None
    assert saved_trip.route.bus_line == "8000"
    assert saved_trip.route.bus_direction == 1
