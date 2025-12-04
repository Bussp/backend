from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.repositories.history_repository_adapter import (
    UserHistoryRepositoryAdapter,
)


class _DummyTrip:
    def __init__(self, email: str, bus_line: str, bus_direction: int, score: int) -> None:
        self.email = email
        self.bus_line = bus_line
        self.bus_direction = bus_direction
        self.distance = 100
        self.score = score
        self.trip_datetime = datetime(2025, 1, 1)


class _DummyUser:
    def __init__(self, email: str, trips: list[_DummyTrip] | None):
        self.email = email
        self.trips = trips or []


class _DummyResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


@pytest.fixture(scope="function")
async def db_session_transactional() -> AsyncGenerator[AsyncSession, None]:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from src.adapters.database.connection import engine

    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            session_factory = async_sessionmaker(
                bind=conn, class_=AsyncSession, expire_on_commit=False
            )
            async with session_factory() as session:
                yield session
        finally:
            await trans.rollback()


@pytest.mark.asyncio
async def test_get_user_history_returns_history_using_autospec() -> None:
    session = AsyncMock()

    trip = _DummyTrip(email="alice@example.com", bus_line="8000", bus_direction=1, score=12)
    user_db = _DummyUser(email="alice@example.com", trips=[trip])

    session.execute = AsyncMock(return_value=_DummyResult(user_db))

    adapter = UserHistoryRepositoryAdapter(session)

    history = await adapter.get_user_history("alice@example.com")

    assert history is not None
    assert history.email == "alice@example.com"
    assert len(history.trips) == 1
    assert history.trips[0].route.bus_line == "8000"
    assert history.trips[0].route.bus_direction == 1
    assert history.trips[0].score == 12


@pytest.mark.asyncio
async def test_get_user_history_returns_none_when_missing_or_no_trips() -> None:
    session_none = AsyncMock()
    session_none.execute = AsyncMock(return_value=_DummyResult(None))
    adapter_none = UserHistoryRepositoryAdapter(session_none)

    history_none = await adapter_none.get_user_history("noone@example.com")
    assert history_none is None

    session_empty = AsyncMock()
    user_empty = _DummyUser(email="empty@example.com", trips=[])
    session_empty.execute = AsyncMock(return_value=_DummyResult(user_empty))
    adapter_empty = UserHistoryRepositoryAdapter(session_empty)

    history_empty = await adapter_empty.get_user_history("empty@example.com")
    assert history_empty is None


@pytest.mark.asyncio
async def test_get_user_history_with_multiple_trips_returns_all_route_identifiers() -> None:
    session = AsyncMock()

    trips = [
        _DummyTrip(email="multi@example.com", bus_line="8000", bus_direction=1, score=10),
        _DummyTrip(email="multi@example.com", bus_line="9000", bus_direction=2, score=20),
        _DummyTrip(email="multi@example.com", bus_line="7000", bus_direction=1, score=30),
    ]
    user_db = _DummyUser(email="multi@example.com", trips=trips)

    session.execute = AsyncMock(return_value=_DummyResult(user_db))

    adapter = UserHistoryRepositoryAdapter(session)

    history = await adapter.get_user_history("multi@example.com")

    assert history is not None
    assert len(history.trips) == 3

    route_data = [(trip.route.bus_line, trip.route.bus_direction) for trip in history.trips]
    assert ("8000", 1) in route_data
    assert ("9000", 2) in route_data
    assert ("7000", 1) in route_data
