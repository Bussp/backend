from datetime import UTC, datetime
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.bus import RouteIdentifier
from src.core.models.trip import Trip
from src.core.models.user_history import HistoryEntry, UserHistory
from src.core.ports.history_repository import UserHistoryRepository
from src.core.services.history_service import HistoryService


@pytest.mark.asyncio
async def test_get_user_history_timezone_aware() -> None:
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip_date = datetime(2025, 10, 16, 10, 0, 0, tzinfo=UTC)
    trip = Trip(
        email="tz@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=1000,
        score=10,
        trip_date=trip_date,
    )

    user_history = UserHistory(email="tz@example.com", trips=[trip])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    result = await service.get_user_history("tz@example.com")

    assert len(result) == 1
    assert result[0].date == trip_date
    assert result[0].score == 10
    assert result[0].route.bus_line == "8000"
    assert result[0].route.bus_direction == 1
    history_repo.get_user_history.assert_awaited_once_with("tz@example.com")


@pytest.mark.asyncio
async def test_get_user_history_no_data() -> None:
    history_repo = create_autospec(UserHistoryRepository, instance=True)
    history_repo.get_user_history = AsyncMock(return_value=None)

    service = HistoryService(history_repo)

    result = await service.get_user_history("noone@example.com")

    assert result == []
    history_repo.get_user_history.assert_awaited_once_with("noone@example.com")


@pytest.mark.asyncio
async def test_get_user_history_single_entry() -> None:
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip_date = datetime(2025, 10, 16, 10, 0, 0)
    trip = Trip(
        email="test@example.com",
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=1000,
        score=10,
        trip_date=trip_date,
    )

    user_history = UserHistory(email="test@example.com", trips=[trip])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    result = await service.get_user_history("test@example.com")

    assert len(result) == 1
    assert result[0].date == trip_date
    assert result[0].score == 10
    assert result[0].route.bus_line == "8000"
    assert result[0].route.bus_direction == 1
    history_repo.get_user_history.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_user_history_multiple_entries() -> None:
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip1_date = datetime(2025, 10, 16, 10, 0, 0)
    trip2_date = datetime(2025, 10, 17, 14, 30, 0)
    trip3_date = datetime(2025, 10, 18, 8, 15, 0)

    trips = [
        Trip(
            email="multi@example.com",
            route=RouteIdentifier(bus_line="8000", bus_direction=1),
            distance=1000,
            score=10,
            trip_date=trip1_date,
        ),
        Trip(
            email="multi@example.com",
            route=RouteIdentifier(bus_line="9000", bus_direction=2),
            distance=2000,
            score=20,
            trip_date=trip2_date,
        ),
        Trip(
            email="multi@example.com",
            route=RouteIdentifier(bus_line="7000", bus_direction=1),
            distance=3000,
            score=30,
            trip_date=trip3_date,
        ),
    ]

    user_history = UserHistory(email="multi@example.com", trips=trips)

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    result = await service.get_user_history("multi@example.com")

    assert len(result) == 3
    assert all(isinstance(entry, HistoryEntry) for entry in result)

    assert result[0].date == trip1_date
    assert result[0].score == 10
    assert result[0].route.bus_line == "8000"
    assert result[0].route.bus_direction == 1

    assert result[1].date == trip2_date
    assert result[1].score == 20
    assert result[1].route.bus_line == "9000"
    assert result[1].route.bus_direction == 2

    assert result[2].date == trip3_date
    assert result[2].score == 30
    assert result[2].route.bus_line == "7000"
    assert result[2].route.bus_direction == 1


@pytest.mark.asyncio
async def test_get_user_history_empty_trips() -> None:
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    user_history = UserHistory(email="empty@example.com", trips=[])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    result = await service.get_user_history("empty@example.com")

    assert result == []
    history_repo.get_user_history.assert_awaited_once_with("empty@example.com")
