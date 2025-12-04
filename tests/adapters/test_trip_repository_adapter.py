from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.adapters.database.connection import engine
from src.core.models.bus import RouteIdentifier
from src.core.models.trip import Trip as DomainTrip


@pytest.fixture(scope="function")
async def db_session_transactional() -> AsyncGenerator:
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
        route=RouteIdentifier(bus_line="8000", bus_direction=1),
        distance=1000,
        score=10,
        trip_datetime=datetime(2025, 1, 1, 8, 0, 0),
    )


@pytest.mark.asyncio
async def test_save_trip_unit(monkeypatch) -> None:
    import importlib

    adapter_mod = importlib.import_module("src.adapters.repositories.trip_repository_adapter")

    dummy_db_obj = SimpleNamespace(
        email="u@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        score=10,
        trip_datetime=datetime(2025, 1, 1, 8, 0, 0),
    )

    monkeypatch.setattr(adapter_mod, "map_trip_domain_to_db", lambda t: dummy_db_obj)

    monkeypatch.setattr(
        adapter_mod,
        "map_trip_db_to_domain",
        lambda db: DomainTrip(
            email=db.email,
            route=RouteIdentifier(
                bus_line=db.bus_line,
                bus_direction=db.bus_direction,
            ),
            distance=db.distance,
            score=db.score,
            trip_datetime=db.trip_datetime,
        ),
    )

    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = Mock()

    adapter = adapter_mod.TripRepositoryAdapter(session)

    domain_trip = _make_domain_trip()

    saved = await adapter.save_trip(domain_trip)

    session.add.assert_called_once_with(dummy_db_obj)
    session.flush.assert_awaited()

    assert isinstance(saved, DomainTrip)
    assert saved.email == "u@example.com"
    assert saved.route.bus_line == "8000"
    assert saved.score == 10
