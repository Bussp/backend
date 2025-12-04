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
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

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
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

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
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

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
    service: RouteService = RouteService(
        bus_provider=bus_provider, gtfs_repository=gtfs_repo
    )

    # Act / Assert
    with pytest.raises(RuntimeError, match="auth failed"):
        await service.get_route_details(route_identifier)

    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_route_details.assert_not_awaited()


def test_get_route_shape_found() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route = RouteIdentifier(bus_line="1012-10", bus_direction=1)

    # Create a mock route shape
    mock_shape = RouteShape(
        route=route,
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
    result = service.get_route_shape(route)

    # Assert
    assert result is not None
    assert result.route.bus_line == "1012-10"
    assert result.route.bus_direction == 1
    assert result.shape_id == "84609"
    assert len(result.points) == 2
    gtfs_repo.get_route_shape.assert_called_once_with(route)


def test_get_route_shape_not_found() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route = RouteIdentifier(bus_line="nonexistent-route", bus_direction=1)

    gtfs_repo.get_route_shape.return_value = None

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shape(route)

    # Assert
    assert result is None
    gtfs_repo.get_route_shape.assert_called_once_with(route)


def test_get_route_shape_with_many_points() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route = RouteIdentifier(bus_line="long-route", bus_direction=1)

    # Create a shape with many points
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

    mock_shape = RouteShape(route=route, shape_id="shape_long", points=points)

    gtfs_repo.get_route_shape.return_value = mock_shape

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shape(route)

    # Assert
    assert result is not None
    assert len(result.points) == 100
    assert result.points[0].sequence == 1
    assert result.points[99].sequence == 100
    gtfs_repo.get_route_shape.assert_called_once_with(route)


def test_get_route_shape_with_special_characters() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route = RouteIdentifier(bus_line="route-with-special_chars@123", bus_direction=1)

    mock_shape = RouteShape(
        route=route,
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
    result = service.get_route_shape(route)

    # Assert
    assert result is not None
    assert result.route.bus_line == "route-with-special_chars@123"
    gtfs_repo.get_route_shape.assert_called_once_with(route)


def test_get_route_shape_independent_of_bus_provider() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route = RouteIdentifier(bus_line="test-route", bus_direction=1)

    mock_shape = RouteShape(
        route=route,
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
    result = service.get_route_shape(route)

    # Assert
    assert result is not None
    # Verify bus_provider was not called at all
    bus_provider.authenticate.assert_not_called()
    bus_provider.get_bus_positions.assert_not_called()
    bus_provider.get_route_details.assert_not_called()


def test_get_route_shapes_multiple_routes() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route1 = RouteIdentifier(bus_line="8075", bus_direction=1)
    route2 = RouteIdentifier(bus_line="8075", bus_direction=2)
    route3 = RouteIdentifier(bus_line="1012", bus_direction=1)

    mock_shape1 = RouteShape(
        route=route1,
        shape_id="shape_8075_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    mock_shape2 = RouteShape(
        route=route2,
        shape_id="shape_8075_2",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5510, longitude=-46.6340),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    mock_shape3 = RouteShape(
        route=route3,
        shape_id="shape_1012_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5515, longitude=-46.6345),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    gtfs_repo.get_route_shape.side_effect = [mock_shape1, mock_shape2, mock_shape3]

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shapes([route1, route2, route3])

    # Assert
    assert len(result) == 3
    assert result[0].route.bus_line == "8075"
    assert result[0].route.bus_direction == 1
    assert result[1].route.bus_line == "8075"
    assert result[1].route.bus_direction == 2
    assert result[2].route.bus_line == "1012"
    assert result[2].route.bus_direction == 1


def test_get_route_shapes_partial_results() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    route1 = RouteIdentifier(bus_line="8075", bus_direction=1)
    route2 = RouteIdentifier(bus_line="nonexistent", bus_direction=1)
    route3 = RouteIdentifier(bus_line="1012", bus_direction=1)

    mock_shape1 = RouteShape(
        route=route1,
        shape_id="shape_8075_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    mock_shape3 = RouteShape(
        route=route3,
        shape_id="shape_1012_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5515, longitude=-46.6345),
                sequence=1,
                distance_traveled=0.0,
            )
        ],
    )

    # Second route returns None (not found)
    gtfs_repo.get_route_shape.side_effect = [mock_shape1, None, mock_shape3]

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shapes([route1, route2, route3])

    # Assert - should only return 2 shapes (excluding the not found one)
    assert len(result) == 2
    assert result[0].route.bus_line == "8075"
    assert result[1].route.bus_line == "1012"


def test_get_route_shapes_empty_list() -> None:
    # Arrange
    bus_provider = create_autospec(BusProviderPort, instance=True)
    gtfs_repo = create_autospec(GTFSRepositoryPort, instance=True)

    service = RouteService(bus_provider, gtfs_repo)

    # Act
    result = service.get_route_shapes([])

    # Assert
    assert result == []
    gtfs_repo.get_route_shape.assert_not_called()
