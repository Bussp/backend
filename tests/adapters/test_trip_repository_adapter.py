"""Tests for TripRepositoryAdapter: unit and integration checks.

Unit test uses AsyncMock and monkeypatch to replace mappers so we don't need
to construct SQLAlchemy ORM objects. Integration test uses a transactional
fixture with lazy imports so it rolls back DB changes and avoids
collection-time SQLAlchemy imports.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.adapters.database.connection import engine
from src.core.models.trip import Trip as DomainTrip


@pytest.fixture(scope="function")
async def db_session_transactional() -> AsyncGenerator:
    """Transactional session fixture with lazy SQLAlchemy imports.

    Yields an AsyncSession bound to a connection inside a transaction which
    will be rolled back at teardown.
    """
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


def _make_domain_trip() -> object:
    from src.core.models.trip import Trip

    return Trip(
        email="u@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        start_date=datetime(2025, 1, 1, 8, 0, 0),
        end_date=datetime(2025, 1, 1, 9, 0, 0),
    )


@pytest.mark.asyncio
async def test_save_trip_unit(monkeypatch) -> None:
    """Unit test: ensure save_trip adds the mapped DB object and flushes.

    We patch the mapper functions inside the adapter module to return a
    simple namespace instead of a real TripDB to avoid SQLAlchemy model
    construction at test time.
    """
    # Lazy import the adapter module so we can patch its attributes
    import importlib

    adapter_mod = importlib.import_module("src.adapters.repositories.trip_repository_adapter")

    # Prepare a dummy "DB" object (would be TripDB in production)
    dummy_db_obj = SimpleNamespace(
        email="u@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        start_date=datetime(2025, 1, 1, 8, 0, 0),
        end_date=datetime(2025, 1, 1, 9, 0, 0),
    )

    # Patch the mappers used by the adapter to avoid SQLAlchemy model usage
    monkeypatch.setattr(adapter_mod, "map_trip_domain_to_db", lambda t: dummy_db_obj)
    # map_trip_db_to_domain should convert the dummy_db_obj back to a domain Trip

    monkeypatch.setattr(
        adapter_mod,
        "map_trip_db_to_domain",
        lambda db: DomainTrip(
            email=db.email,
            bus_line=db.bus_line,
            bus_direction=db.bus_direction,
            distance=db.distance,
            score=db.score,
            start_date=db.start_date,
            end_date=db.end_date,
        ),
    )

    # Create an AsyncMock session with a flush coroutine. Make add a plain
    # callable (not a coroutine) because the adapter calls session.add() sync.
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = Mock()

    adapter = adapter_mod.TripRepositoryAdapter(session)

    domain_trip = _make_domain_trip()

    # Act
    saved = await adapter.save_trip(domain_trip)

    # Assert: session.add called with the dummy DB object and flush awaited
    session.add.assert_called_once_with(dummy_db_obj)
    session.flush.assert_awaited()

    assert isinstance(saved, DomainTrip)
    assert saved.email == "u@example.com"
    assert saved.bus_line == "8000"
    assert saved.score == 10
