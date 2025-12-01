"""Tests for RouteService.

This file contains two groups of tests:
- async tests that exercise the bus provider (authenticate, get_bus_positions, get_route_details)
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
async def test_get_bus_positions_calls_auth_and_provider() -> None:
    # Arrange
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.authenticate = AsyncMock(return_value=True)
    raw_provider.get_bus_positions = AsyncMock()

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    route_identifier: RouteIdentifier = RouteIdentifier(
        bus_line="8075",
        bus_direction=1,
    )

    bus_route: BusRoute = BusRoute(
        route_id=1234,
        route=route_identifier,
    )

    expected_positions: list[BusPosition] = [
        BusPosition(
            route=route_identifier,
            position=Coordinate(latitude=-23.0, longitude=-46.0),
            time_updated=datetime.now(UTC),
        ),
    ]

    # configurando retorno tipado do mock
    raw_provider.get_bus_positions.return_value = expected_positions

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(bus_provider=bus_provider, gtfs_repository=gtfs_repo)

    # Act
    result: list[BusPosition] = await service.get_bus_positions(bus_route)

    # Assert
    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_bus_positions.assert_awaited_once_with(bus_route)
    assert result == expected_positions


@pytest.mark.asyncio
async def test_get_route_details_calls_auth_and_provider() -> None:
    # Arrange
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.authenticate = AsyncMock(return_value=True)
    raw_provider.get_route_details = AsyncMock()

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

    # agora o provider também retorna lista
    raw_provider.get_route_details.return_value = expected_routes

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(bus_provider=bus_provider, gtfs_repository=gtfs_repo)

    # Act
    result: list[BusRoute] = await service.get_route_details(route_identifier)

    # Assert
    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_route_details.assert_awaited_once_with(route_identifier)
    assert result == expected_routes


@pytest.mark.asyncio
async def test_get_bus_positions_propagates_exception_from_provider() -> None:
    # Arrange
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.authenticate = AsyncMock(return_value=True)
    raw_provider.get_bus_positions = AsyncMock(side_effect=RuntimeError("boom"))

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    route_identifier: RouteIdentifier = RouteIdentifier(
        bus_line="8075",
        bus_direction=1,
    )

    bus_route: BusRoute = BusRoute(
        route_id=1234,
        route=route_identifier,
    )

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(bus_provider=bus_provider, gtfs_repository=gtfs_repo)

    # Act / Assert
    with pytest.raises(RuntimeError, match="boom"):
        await service.get_bus_positions(bus_route)

    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_bus_positions.assert_awaited_once_with(bus_route)


@pytest.mark.asyncio
async def test_get_route_details_propagates_exception_from_authenticate() -> None:
    # Arrange
    raw_provider: Mock = Mock(spec=BusProviderPort)
    raw_provider.authenticate = AsyncMock(
        side_effect=RuntimeError("auth failed"),
    )
    raw_provider.get_route_details = AsyncMock()

    bus_provider: BusProviderPort = cast(BusProviderPort, raw_provider)

    route_identifier: RouteIdentifier = RouteIdentifier(
        bus_line="8075",
        bus_direction=1,
    )

    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)
    service: RouteService = RouteService(bus_provider=bus_provider, gtfs_repository=gtfs_repo)

    # Act / Assert
    with pytest.raises(RuntimeError, match="auth failed"):
        await service.get_route_details(route_identifier)

    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_route_details.assert_not_awaited()


def test_get_route_shape_found() -> None:
    """Test getting a route shape when it exists."""
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    # Create a mock route shape
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

    # Act
    result = service.get_route_shape("1012-10")

    # Assert
    assert result is not None
    assert result.route_id == "1012-10"
    assert result.shape_id == "84609"
    assert len(result.points) == 2
    gtfs_repo.get_route_shape.assert_called_once_with("1012-10")


def test_get_route_shape_not_found() -> None:
    """Test getting a route shape when it doesn't exist."""
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    gtfs_repo.get_route_shape.return_value = None

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shape("nonexistent-route")

    # Assert
    assert result is None
    gtfs_repo.get_route_shape.assert_called_once_with("nonexistent-route")


def test_get_route_shape_with_many_points() -> None:
    """Test getting a route shape with many coordinate points."""
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    # Create a shape with many points
    points = [
        RouteShapePoint(
            coordinate=Coordinate(latitude=-23.5505 + i * 0.001, longitude=-46.6333 + i * 0.001),
            sequence=i + 1,
            distance_traveled=float(i * 10),
        )
        for i in range(100)
    ]

    mock_shape = RouteShape(route_id="long-route", shape_id="shape_long", points=points)

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shape("long-route")

    # Assert
    assert result is not None
    assert len(result.points) == 100
    assert result.points[0].sequence == 1
    assert result.points[99].sequence == 100
    gtfs_repo.get_route_shape.assert_called_once_with("long-route")


def test_get_route_shape_with_special_characters() -> None:
    """Test getting a route shape with special characters in route ID."""
    # Arrange
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

    # Act
    result = service.get_route_shape("route-with-special_chars@123")

    # Assert
    assert result is not None
    assert result.route_id == "route-with-special_chars@123"
    gtfs_repo.get_route_shape.assert_called_once_with("route-with-special_chars@123")


def test_get_route_shape_independent_of_bus_provider() -> None:
    """Test that get_route_shape doesn't interact with bus provider."""
    # Arrange
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

    # Act
    result = service.get_route_shape("test-route")

    # Assert
    assert result is not None
    # Verify bus_provider was not called at all
    bus_provider.authenticate.assert_not_called()
    bus_provider.get_bus_positions.assert_not_called()
    bus_provider.get_route_details.assert_not_called()
