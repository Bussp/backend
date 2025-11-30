"""Tests for RouteService.get_route_shape method.

These tests verify that the RouteService correctly delegates to the
GTFS repository and handles the response.
"""

from unittest.mock import MagicMock, create_autospec

import pytest

from src.core.models.coordinate import Coordinate
from src.core.models.route_shape import RouteShape, RouteShapePoint
from src.core.ports.bus_provider_port import BusProviderPort
from src.core.ports.gtfs_repository import GTFSRepositoryPort
from src.core.services.route_service import RouteService


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

    service = RouteService(bus_provider, gtfs_repo)  # type: ignore[arg-type]

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

    service = RouteService(bus_provider, gtfs_repo)  # type: ignore[arg-type]

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

    service = RouteService(bus_provider, gtfs_repo)  # type: ignore[arg-type]

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

    service = RouteService(bus_provider, gtfs_repo)  # type: ignore[arg-type]

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

    service = RouteService(bus_provider, gtfs_repo)  # type: ignore[arg-type]

    # Act
    result = service.get_route_shape("test-route")

    # Assert
    assert result is not None
    # Verify bus_provider was not called at all
    bus_provider.authenticate.assert_not_called()
    bus_provider.get_bus_positions.assert_not_called()
    bus_provider.get_route_details.assert_not_called()
