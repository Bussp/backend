"""Tests for UserHistoryRepositoryAdapter using example-based patterns.

These tests follow the style used in `tests/core/test_trip_service_example.py`:
- use `create_autospec` for interfaces where appropriate
- use `AsyncMock` to simulate async behaviors

They avoid real DB IO by autospeccing/mocking the AsyncSession execute
to return an object with `scalar_one_or_none()`.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, create_autospec

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.repositories.history_repository_adapter import (
    UserHistoryRepositoryAdapter,
)


class _DummyTrip:
    def __init__(self, email: str, bus_line: str, score: int) -> None:
        self.email = email
        self.bus_line = bus_line
        self.bus_direction = 1
        self.distance = 100
        self.score = score
        self.start_date = datetime(2025, 1, 1)
        self.end_date = datetime(2025, 1, 1, 1)


class _DummyUser:
    def __init__(self, email: str, trips: list[_DummyTrip] | None):
        self.email = email
        self.trips = trips or []


class _DummyResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_get_user_history_returns_history_using_autospec() -> None:
    """Adapter should return a mapped UserHistory when DB returns a user with trips."""
    # Arrange
    # Autospec the AsyncSession interface so the mock matches the real API.
    session = create_autospec(AsyncSession, instance=True)

    trip = _DummyTrip(email="alice@example.com", bus_line="8000", score=12)
    user_db = _DummyUser(email="alice@example.com", trips=[trip])

    # Mock execute to be async and return an object with scalar_one_or_none()
    session.execute = AsyncMock(return_value=_DummyResult(user_db))  # type: ignore[attr-defined]

    adapter = UserHistoryRepositoryAdapter(session)  # type: ignore[arg-type]

    # Act
    history = await adapter.get_user_history("alice@example.com")

    # Assert
    assert history is not None
    assert history.email == "alice@example.com"
    assert len(history.trips) == 1
    assert history.trips[0].bus_line == "8000"
    assert history.trips[0].score == 12


@pytest.mark.asyncio
async def test_get_user_history_returns_none_when_missing_or_no_trips() -> None:
    """Adapter should return None when DB returns None or when user.trips is empty."""
    # Arrange: case where execute returns None
    session_none = create_autospec(AsyncSession, instance=True)
    session_none.execute = AsyncMock(return_value=_DummyResult(None))  # type: ignore[attr-defined]
    adapter_none = UserHistoryRepositoryAdapter(session_none)  # type: ignore[arg-type]

    # Act & Assert
    history_none = await adapter_none.get_user_history("noone@example.com")
    assert history_none is None

    # Arrange: user exists but has empty trips
    session_empty = create_autospec(AsyncSession, instance=True)
    user_empty = _DummyUser(email="empty@example.com", trips=[])
    session_empty.execute = AsyncMock(return_value=_DummyResult(user_empty))  # type: ignore[attr-defined]
    adapter_empty = UserHistoryRepositoryAdapter(session_empty)  # type: ignore[arg-type]

    # Act & Assert
    history_empty = await adapter_empty.get_user_history("empty@example.com")
    assert history_empty is None
