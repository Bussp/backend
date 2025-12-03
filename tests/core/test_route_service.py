"""Tests for RouteService.

This file contains two groups of tests:
- async tests that exercise the bus provider (get_bus_positions, search_routes)
- sync tests that exercise get_route_shape delegating to a GTFS repository
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.models.route_shape import RouteShape, RouteShapePoint
from src.core.ports.bus_provider_port import BusProviderPort
from src.core.ports.gtfs_repository import GTFSRepositoryPort
from src.core.services.route_service import RouteService


@pytest.mark.asyncio
async def test_get_bus_positions_calls_provider() -> None:
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.get_bus_positions = AsyncMock()

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    route_identifier: RouteIdentifier = RouteIdentifier(
        bus_line="8075-10",
        bus_direction=1,
    )

    expected_positions: list[BusPosition] = [
        BusPosition(
            route=route_identifier,
            position=Coordinate(latitude=-23.0, longitude=-46.0),
            time_updated=datetime.now(UTC),
        ),
    ]

    raw_provider.get_bus_positions.return_value = expected_positions

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

    routes = [
        BusRoute(route_id=1234, route=route_identifier),
    ]
    result: list[BusPosition] = await service.get_bus_positions(routes)

    raw_provider.get_bus_positions.assert_awaited_once_with(routes)
    assert result == expected_positions


@pytest.mark.asyncio
async def test_search_routes_calls_provider() -> None:
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.search_routes = AsyncMock()

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    route_identifier: RouteIdentifier = RouteIdentifier(
        bus_line="8075",
        bus_direction=1,
    )

    expected_bus_route: BusRoute = BusRoute(
        route_id=1234,
        route=route_identifier,
    )

    expected_routes: list[BusRoute] = [expected_bus_route]

    raw_provider.search_routes.return_value = expected_routes

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

    query = "8075"
    result: list[BusRoute] = await service.search_routes(query)

    raw_provider.search_routes.assert_awaited_once_with(query)
    assert result == expected_routes


@pytest.mark.asyncio
async def test_get_bus_positions_propagates_exception_from_provider() -> None:
    """Test that exceptions from the provider are propagated."""
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.get_bus_positions = AsyncMock(side_effect=RuntimeError("boom"))

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

    routes = [
        BusRoute(
            route_id=1234,
            route=RouteIdentifier(bus_line="8075-10", bus_direction=1),
        ),
    ]

    with pytest.raises(RuntimeError, match="boom"):
        await service.get_bus_positions(routes)

    raw_provider.get_bus_positions.assert_awaited_once_with(routes)


@pytest.mark.asyncio
async def test_search_routes_propagates_exception_from_provider() -> None:
    """Test that exceptions from search_routes are propagated."""
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.search_routes = AsyncMock(side_effect=RuntimeError("search failed"))

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

    with pytest.raises(RuntimeError, match="search failed"):
        await service.search_routes("8075")

    raw_provider.search_routes.assert_awaited_once_with("8075")


def test_get_route_shape_found() -> None:
    """Test getting a route shape when it exists."""
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    mock_shape = RouteShape(
        route_id="1012-10",
        shape_id="84609",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            ),
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5510, longitude=-46.6340),
                sequence=2,
                distance_traveled=10.5,
            ),
        ],
    )

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    result = service.get_route_shape("1012-10")

    assert result is not None
    assert result.route_id == "1012-10"
    assert result.shape_id == "84609"
    assert len(result.points) == 2
    gtfs_repo.get_route_shape.assert_called_once_with("1012-10")


def test_get_route_shape_not_found() -> None:
    """Test getting a route shape when it doesn't exist."""
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    gtfs_repo.get_route_shape.return_value = None

    service = RouteService(bus_provider, gtfs_repo)

    result = service.get_route_shape("nonexistent-route")

    assert result is None
    gtfs_repo.get_route_shape.assert_called_once_with("nonexistent-route")


def test_get_route_shape_with_many_points() -> None:
    """Test getting a route shape with many coordinate points."""
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    points = [
        RouteShapePoint(
            coordinate=Coordinate(
                latitude=-23.5505 + i * 0.001, longitude=-46.6333 + i * 0.001
            ),
            sequence=i + 1,
            distance_traveled=float(i * 10),
        )
        for i in range(100)
    ]

    mock_shape = RouteShape(route_id="long-route", shape_id="shape_long", points=points)

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    result = service.get_route_shape("long-route")

    assert result is not None
    assert len(result.points) == 100
    assert result.points[0].sequence == 1
    assert result.points[99].sequence == 100
    gtfs_repo.get_route_shape.assert_called_once_with("long-route")


def test_get_route_shape_with_special_characters() -> None:
    """Test getting a route shape with special characters in route ID."""
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    mock_shape = RouteShape(
        route_id="route-with-special_chars@123",
        shape_id="shape_special",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    result = service.get_route_shape("route-with-special_chars@123")

    assert result is not None
    assert result.route_id == "route-with-special_chars@123"
    gtfs_repo.get_route_shape.assert_called_once_with("route-with-special_chars@123")


def test_get_route_shape_independent_of_bus_provider() -> None:
    """Test that get_route_shape doesn't interact with bus provider."""
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    mock_shape = RouteShape(
        route_id="test-route",
        shape_id="test-shape",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    result = service.get_route_shape("test-route")

    assert result is not None
    bus_provider.get_bus_positions.assert_not_called()
    bus_provider.search_routes.assert_not_called()
