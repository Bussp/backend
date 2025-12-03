"""Unit tests for HistoryService.

Two tests:
- when repository has no data -> get_user_history_summary returns ([], [])
- when repository has a single trip -> returns that trip's date and score
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.trip import Trip
from src.core.models.user_history import UserHistory
from src.core.ports.history_repository import UserHistoryRepository
from src.core.services.history_service import HistoryService


@pytest.mark.asyncio
async def test_get_user_history_summary_no_data() -> None:
    """When repository returns None, summary should be empty lists."""
    # Arrange
    history_repo = create_autospec(UserHistoryRepository, instance=True)
    history_repo.get_user_history = AsyncMock(return_value=None)

    service = HistoryService(history_repo)

    # Act
    summary_dates, summary_scores = await service.get_user_history_summary("noone@example.com")

    # Assert
    assert summary_dates == []
    assert summary_scores == []
    history_repo.get_user_history.assert_awaited_once_with("noone@example.com")


@pytest.mark.asyncio
async def test_get_user_history_summary_single_entry() -> None:
    """When repository returns a UserHistory with one Trip, summary should contain that trip's date and score."""
    # Arrange
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip_date = datetime(2025, 10, 16, 10, 0, 0)
    trip = Trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        start_date=trip_date,
        end_date=trip_date,
    )

    user_history = UserHistory(email="test@example.com", trips=[trip])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    # Act
    summary_dates, summary_scores = await service.get_user_history_summary("test@example.com")

    # Assert
    assert summary_dates == [trip_date]
    assert summary_scores == [10]
    history_repo.get_user_history.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_user_history_summary_timezone_aware() -> None:
    """Ensure the service returns timezone-aware datetimes unchanged (use UTC here)."""
    # Arrange
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip_date = datetime(2025, 10, 16, 10, 0, 0, tzinfo=UTC)
    trip = Trip(
        email="tz@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        start_date=trip_date,
        end_date=trip_date,
    )

    user_history = UserHistory(email="tz@example.com", trips=[trip])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    # Act
    dates, scores = await service.get_user_history_summary("tz@example.com")

    # Assert
    assert dates == [trip_date]
    assert scores == [10]
    history_repo.get_user_history.assert_awaited_once_with("tz@example.com")


@pytest.mark.asyncio
async def test_get_user_history_no_data() -> None:
    """When repository returns None, get_user_history should return None."""
    # Arrange
    history_repo = create_autospec(UserHistoryRepository, instance=True)
    history_repo.get_user_history = AsyncMock(return_value=None)

    service = HistoryService(history_repo)

    # Act
    result = await service.get_user_history("noone@example.com")

    # Assert
    assert result is None
    history_repo.get_user_history.assert_awaited_once_with("noone@example.com")


@pytest.mark.asyncio
async def test_get_user_history_single_entry() -> None:
    """When repository returns a UserHistory with one Trip, get_user_history should return that UserHistory."""
    # Arrange
    history_repo = create_autospec(UserHistoryRepository, instance=True)

    trip_date = datetime(2025, 10, 16, 10, 0, 0)
    trip = Trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        start_date=trip_date,
        end_date=trip_date,
    )

    user_history = UserHistory(email="test@example.com", trips=[trip])

    history_repo.get_user_history = AsyncMock(return_value=user_history)

    service = HistoryService(history_repo)

    # Act
    result = await service.get_user_history("test@example.com")

    # Assert
    assert result == user_history
    history_repo.get_user_history.assert_awaited_once_with("test@example.com")
