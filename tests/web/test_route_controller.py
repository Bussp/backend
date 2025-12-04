from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.models.user import User
from src.core.services.route_service import RouteService
from src.main import app
from src.web.auth import get_current_user
from src.web.controllers.route_controller import get_route_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_service() -> RouteService:
    service = AsyncMock(spec=RouteService)
    typed_service: RouteService = service
    typed_service.search_routes = AsyncMock()  # type: ignore[method-assign]
    typed_service.get_bus_positions = AsyncMock()  # type: ignore[method-assign]
    return typed_service


@pytest.fixture
def mock_current_user() -> User:
    return User(name="Test User", email="test@example.com", score=0)


@pytest.fixture(autouse=True)
def override_dependency(
    mock_service: RouteService, mock_current_user: User
) -> Generator[None, None, None]:
    app.dependency_overrides[get_route_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.clear()


class TestSearchRoutes:
    @pytest.mark.asyncio
    async def test_search_endpoint_success(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        bus_route_1 = BusRoute(
            route_id=2044,
            route=RouteIdentifier(
                bus_line="8075",
                bus_direction=1,
            ),
            is_circular=False,
            terminal_name="Terminal A",
        )
        bus_route_2 = BusRoute(
            route_id=34812,
            route=RouteIdentifier(
                bus_line="8075",
                bus_direction=2,
            ),
            is_circular=False,
            terminal_name="Terminal B",
        )

        mock_service.search_routes.return_value = [bus_route_1, bus_route_2]  # type: ignore[attr-defined]

        response = client.get("/routes/search", params={"query": "8075"})

        assert response.status_code == 200
        data = response.json()

        assert "routes" in data
        assert len(data["routes"]) == 2

        routes = data["routes"]

        assert routes[0]["route_id"] == 2044
        assert routes[0]["route"]["bus_line"] == "8075"

        assert routes[1]["route_id"] == 34812
        assert routes[1]["route"]["bus_line"] == "8075"

        mock_service.search_routes.assert_awaited_once()  # type: ignore[attr-defined]
        called_arg = mock_service.search_routes.await_args.args[0]  # type: ignore[attr-defined]
        assert called_arg == "8075"

    @pytest.mark.asyncio
    async def test_search_endpoint_with_destination_name(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test search with destination name query."""
        route_identifier = RouteIdentifier(
            bus_line="809",
            bus_direction=1,
        )
        bus_route = BusRoute(
            route_id=1234,
            route=route_identifier,
            is_circular=False,
            terminal_name="Vila Nova Conceição",
        )

        mock_service.search_routes.return_value = [bus_route]  # type: ignore[attr-defined]

        response = client.get("/routes/search", params={"query": "Vila Nova Conceição"})

        assert response.status_code == 200
        data = response.json()

        assert "routes" in data
        assert len(data["routes"]) == 1

        mock_service.search_routes.assert_awaited_once()  # type: ignore[attr-defined]
        called_arg = mock_service.search_routes.await_args.args[0]  # type: ignore[attr-defined]
        assert called_arg == "Vila Nova Conceição"

    @pytest.mark.asyncio
    async def test_search_endpoint_empty_results(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test search returning empty results."""
        mock_service.search_routes.return_value = []  # type: ignore[attr-defined]

        response = client.get("/routes/search", params={"query": "UNKNOWN"})

        assert response.status_code == 200
        data = response.json()
        assert data["routes"] == []

    @pytest.mark.asyncio
    async def test_search_endpoint_error_returns_500(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test that service exception returns 500 error."""
        mock_service.search_routes.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

        response = client.get("/routes/search", params={"query": "8075"})

        assert response.status_code == 500
        body = response.json()
        assert "Failed to search routes" in body["detail"]


class TestBusPositions:
    """Tests for the /routes/positions endpoint."""

    @pytest.mark.asyncio
    async def test_positions_endpoint_success(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test successful positions retrieval."""
        position = BusPosition(
            route_id=2044,
            position=Coordinate(latitude=-23.5, longitude=-46.6),
            time_updated=datetime.now(UTC),
        )

        mock_service.get_bus_positions.return_value = [position]  # type: ignore[attr-defined]

        payload = {"routes": [{"route_id": 2044}]}

        response = client.post("/routes/positions", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "buses" in data
        assert len(data["buses"]) == 1

        bus = data["buses"][0]

        assert bus["route_id"] == 2044
        assert "position" in bus
        assert "latitude" in bus["position"]
        assert "longitude" in bus["position"]
        assert "time_updated" in bus

        mock_service.get_bus_positions.assert_awaited_once()  # type: ignore[attr-defined]
        # Service now receives route_ids: list[int]
        called_args = mock_service.get_bus_positions.await_args.args  # type: ignore[attr-defined]
        route_ids = called_args[0]
        assert route_ids == [2044]

    @pytest.mark.asyncio
    async def test_positions_endpoint_multiple_routes(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test positions for multiple routes."""
        position1 = BusPosition(
            route_id=2044,
            position=Coordinate(latitude=-23.5, longitude=-46.6),
            time_updated=datetime.now(UTC),
        )
        position2 = BusPosition(
            route_id=5678,
            position=Coordinate(latitude=-23.6, longitude=-46.7),
            time_updated=datetime.now(UTC),
        )

        mock_service.get_bus_positions.return_value = [position1, position2]  # type: ignore[attr-defined]

        payload = {
            "routes": [
                {"route_id": 2044},
                {"route_id": 5678},
            ]
        }

        response = client.post("/routes/positions", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert len(data["buses"]) == 2
        mock_service.get_bus_positions.assert_awaited_once()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_positions_endpoint_error_returns_500(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test that service exception returns 500 error."""
        mock_service.get_bus_positions.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

        payload = {"routes": [{"route_id": 2044}]}

        response = client.post("/routes/positions", json=payload)

        assert response.status_code == 500
        body = response.json()
        assert "Failed to retrieve bus positions" in body["detail"]

    @pytest.mark.asyncio
    async def test_positions_endpoint_empty_routes(
        self, client: TestClient, mock_service: RouteService
    ) -> None:
        """Test positions with empty routes list."""
        mock_service.get_bus_positions.return_value = []  # type: ignore[attr-defined]

        payload = {"routes": []}

        response = client.post("/routes/positions", json=payload)

        assert response.status_code == 200
        assert response.json()["buses"] == []
