"""Tests for GTFSRepositoryAdapter.

These tests verify that the GTFS repository correctly retrieves route shapes
from the SQLite GTFS database.
"""

from unittest.mock import MagicMock, patch

from src.adapters.repositories.gtfs_repository_adapter import GTFSRepositoryAdapter
from src.core.models.bus import RouteIdentifier
from src.core.models.route_shape import RouteShape


def test_get_route_shape_found() -> None:
    # Arrange
    adapter = GTFSRepositoryAdapter()
    route = RouteIdentifier(bus_line="test_route_1", bus_direction=1)

    # Mock the database connection and cursors
    mock_conn = MagicMock()
    mock_cursor1 = MagicMock()
    mock_cursor2 = MagicMock()

    # First query: get shape_id for route
    mock_cursor1.fetchone.return_value = {"shape_id": "test_shape_123"}

    # Second query: get shape points
    mock_cursor2.fetchall.return_value = [
        {
            "shape_pt_lat": -23.5505,
            "shape_pt_lon": -46.6333,
            "shape_pt_sequence": 1,
            "shape_dist_traveled": 0.0,
        },
        {
            "shape_pt_lat": -23.5510,
            "shape_pt_lon": -46.6340,
            "shape_pt_sequence": 2,
            "shape_dist_traveled": 10.5,
        },
        {
            "shape_pt_lat": -23.5515,
            "shape_pt_lon": -46.6345,
            "shape_pt_sequence": 3,
            "shape_dist_traveled": 20.3,
        },
    ]

    # Setup the mock to return different cursors for each execute call
    mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

    # Patch get_gtfs_db to return our mock connection
    with patch("src.adapters.repositories.gtfs_repository_adapter.get_gtfs_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Act
        result = adapter.get_route_shape(route)

    # Assert
    assert result is not None
    assert isinstance(result, RouteShape)
    assert result.route.bus_line == "test_route_1"
    assert result.route.bus_direction == 1
    assert result.shape_id == "test_shape_123"
    assert len(result.points) == 3

    # Check first point
    assert result.points[0].coordinate.latitude == -23.5505
    assert result.points[0].coordinate.longitude == -46.6333
    assert result.points[0].sequence == 1
    assert result.points[0].distance_traveled == 0.0

    # Check last point
    assert result.points[2].coordinate.latitude == -23.5515
    assert result.points[2].coordinate.longitude == -46.6345
    assert result.points[2].sequence == 3
    assert result.points[2].distance_traveled == 20.3


def test_get_route_shape_route_not_found() -> None:
    # Arrange
    adapter = GTFSRepositoryAdapter()
    route = RouteIdentifier(bus_line="nonexistent_route", bus_direction=1)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # First query returns None (route not found)
    mock_cursor.fetchone.return_value = None
    mock_conn.execute.return_value = mock_cursor

    with patch("src.adapters.repositories.gtfs_repository_adapter.get_gtfs_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Act
        result = adapter.get_route_shape(route)

    # Assert
    assert result is None


def test_get_route_shape_no_shape_points() -> None:
    # Arrange
    adapter = GTFSRepositoryAdapter()
    route = RouteIdentifier(bus_line="route_without_points", bus_direction=1)

    mock_conn = MagicMock()
    mock_cursor1 = MagicMock()
    mock_cursor2 = MagicMock()

    # First query: get shape_id for route
    mock_cursor1.fetchone.return_value = {"shape_id": "empty_shape"}

    # Second query: no shape points found
    mock_cursor2.fetchall.return_value = []

    mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

    with patch("src.adapters.repositories.gtfs_repository_adapter.get_gtfs_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Act
        result = adapter.get_route_shape(route)

    # Assert
    assert result is None


def test_get_route_shape_single_point() -> None:
    """Test getting a route shape with only one point."""
    # Arrange
    adapter = GTFSRepositoryAdapter()
    route = RouteIdentifier(bus_line="single_point_route", bus_direction=1)

    mock_conn = MagicMock()
    mock_cursor1 = MagicMock()
    mock_cursor2 = MagicMock()

    mock_cursor1.fetchone.return_value = {"shape_id": "single_point_shape"}

    mock_cursor2.fetchall.return_value = [
        {
            "shape_pt_lat": -23.5505,
            "shape_pt_lon": -46.6333,
            "shape_pt_sequence": 1,
            "shape_dist_traveled": 0.0,
        }
    ]

    mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

    with patch("src.adapters.repositories.gtfs_repository_adapter.get_gtfs_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Act
        result = adapter.get_route_shape(route)

    # Assert
    assert result is not None
    assert len(result.points) == 1
    assert result.points[0].coordinate.latitude == -23.5505
    assert result.points[0].coordinate.longitude == -46.6333


def test_get_route_shape_null_distance_traveled() -> None:
    """Test getting a route shape with NULL distance_traveled values."""
    # Arrange
    adapter = GTFSRepositoryAdapter()
    route = RouteIdentifier(bus_line="route_no_distance", bus_direction=1)

    mock_conn = MagicMock()
    mock_cursor1 = MagicMock()
    mock_cursor2 = MagicMock()

    mock_cursor1.fetchone.return_value = {"shape_id": "shape_no_distance"}

    mock_cursor2.fetchall.return_value = [
        {
            "shape_pt_lat": -23.5505,
            "shape_pt_lon": -46.6333,
            "shape_pt_sequence": 1,
            "shape_dist_traveled": None,
        },
        {
            "shape_pt_lat": -23.5510,
            "shape_pt_lon": -46.6340,
            "shape_pt_sequence": 2,
            "shape_dist_traveled": None,
        },
    ]

    mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

    with patch("src.adapters.repositories.gtfs_repository_adapter.get_gtfs_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Act
        result = adapter.get_route_shape(route)

    # Assert
    assert result is not None
    assert len(result.points) == 2
    assert result.points[0].distance_traveled is None
    assert result.points[1].distance_traveled is None
