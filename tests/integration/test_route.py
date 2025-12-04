from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.web.schemas import (
    BusPositionsRequest,
    BusRouteRequestSchema,
)

from .conftest import create_user_and_login


class TestRouteSearch:
    @pytest.mark.asyncio
    async def test_search_routes_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        mock_bus_routes = [
            BusRoute(
                route_id=12345,
                route=RouteIdentifier(
                    bus_line="8000",
                    bus_direction=1,
                ),
                is_circular=False,
                terminal_name="Terminal A",
            )
        ]

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.search_routes",
            new_callable=AsyncMock,
            return_value=mock_bus_routes,
        ):
            response = await client.get(
                "/routes/search",
                params={"query": "8000"},
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert "routes" in data
            assert len(data["routes"]) == 1

            first_route = data["routes"][0]
            assert "route_id" in first_route
            assert first_route["route_id"] == 12345
            assert "route" in first_route
            assert first_route["route"]["bus_line"] == "8000"
            assert first_route["route"]["bus_direction"] == 1

    @pytest.mark.asyncio
    async def test_search_routes_returns_multiple_results(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        mock_bus_routes = [
            BusRoute(
                route_id=12345,
                route=RouteIdentifier(
                    bus_line="8000",
                    bus_direction=1,
                ),
                is_circular=False,
                terminal_name="Terminal A",
            ),
            BusRoute(
                route_id=12346,
                route=RouteIdentifier(
                    bus_line="8000",
                    bus_direction=2,
                ),
                is_circular=False,
                terminal_name="Terminal B",
            ),
        ]

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.search_routes",
            new_callable=AsyncMock,
            return_value=mock_bus_routes,
        ):
            response = await client.get(
                "/routes/search",
                params={"query": "8000"},
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["routes"]) == 2
            route_ids = [r["route_id"] for r in data["routes"]]
            assert 12345 in route_ids
            assert 12346 in route_ids

    @pytest.mark.asyncio
    async def test_search_routes_returns_empty_for_unknown_query(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.search_routes",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await client.get(
                "/routes/search",
                params={"query": "UNKNOWN"},
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["routes"] == []

    @pytest.mark.asyncio
    async def test_search_routes_returns_500_on_api_error(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.search_routes",
            new_callable=AsyncMock,
            side_effect=RuntimeError("API unavailable"),
        ):
            response = await client.get(
                "/routes/search",
                params={"query": "8000"},
                headers=auth["headers"],
            )

            assert response.status_code == 500
            assert "Failed to search routes" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_search_routes_returns_422_when_query_missing(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        response = await client.get(
            "/routes/search",
            headers=auth["headers"],
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_routes_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/routes/search", params={"query": "8000"})

        assert response.status_code == 401


class TestBusPositions:
    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        mock_positions = [
            BusPosition(
                route_id=12345,
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(UTC),
            ),
            BusPosition(
                route_id=12345,
                position=Coordinate(latitude=-23.551234, longitude=-46.634567),
                time_updated=datetime.now(UTC),
            ),
        ]

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            return_value=mock_positions,
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteRequestSchema(route_id=12345),
                ]
            )

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert "buses" in data
            assert len(data["buses"]) == 2

            first_bus = data["buses"][0]
            assert "route_id" in first_bus
            assert first_bus["route_id"] == 12345
            assert "position" in first_bus
            assert "latitude" in first_bus["position"]
            assert "longitude" in first_bus["position"]
            assert "time_updated" in first_bus

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_500_when_error(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            side_effect=ValueError("Error fetching positions"),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteRequestSchema(route_id=99999),
                ]
            )

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 500
            assert "Failed to retrieve bus positions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_empty_when_no_buses_on_line(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            return_value=[],
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteRequestSchema(route_id=12345),
                ]
            )

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert "buses" in data
            assert len(data["buses"]) == 0

    @pytest.mark.asyncio
    async def test_get_bus_position_works_with_multiple_routes(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        mock_position_12345 = [
            BusPosition(
                route_id=12345,
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(UTC),
            ),
        ]
        mock_position_67890 = [
            BusPosition(
                route_id=67890,
                position=Coordinate(latitude=-23.560520, longitude=-46.643308),
                time_updated=datetime.now(UTC),
            ),
        ]

        def mock_get_positions(route_id: int) -> list[BusPosition]:
            if route_id == 12345:
                return mock_position_12345
            elif route_id == 67890:
                return mock_position_67890
            return []

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            side_effect=mock_get_positions,
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteRequestSchema(route_id=12345),
                    BusRouteRequestSchema(route_id=67890),
                ]
            )

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["buses"]) == 2
            route_ids = [bus["route_id"] for bus in data["buses"]]
            assert 12345 in route_ids
            assert 67890 in route_ids

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_500_when_api_error(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            side_effect=RuntimeError("API error"),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteRequestSchema(route_id=12345),
                ]
            )

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_422_when_invalid_data(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        invalid_request_data: dict[str, list[dict[str, str]]] = {
            "routes": [{"route_id": "not_an_int"}]
        }

        response = await client.post(
            "/routes/positions",
            json=invalid_request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully_with_empty_routes_list(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
            new_callable=AsyncMock,
            return_value=[],
        ):
            request_data = BusPositionsRequest(routes=[])

            response = await client.post(
                "/routes/positions",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            assert response.json()["buses"] == []

    @pytest.mark.asyncio
    async def test_get_bus_position_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        request_data = BusPositionsRequest(
            routes=[
                BusRouteRequestSchema(route_id=12345),
            ]
        )

        response = await client.post("/routes/positions", json=request_data.model_dump())

        assert response.status_code == 401


class TestRouteShape:
    @pytest.mark.asyncio
    async def test_get_route_shape_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        response = await client.get("/routes/shape/1012-10", headers=auth["headers"])

        assert response.status_code == 200
        data = response.json()

        assert data["route_id"] == "1012-10"
        assert "shape_id" in data
        assert "points" in data
        assert len(data["points"]) > 0

        first_point = data["points"][0]
        assert "latitude" in first_point
        assert "longitude" in first_point
        assert isinstance(first_point["latitude"], float)
        assert isinstance(first_point["longitude"], float)

    @pytest.mark.asyncio
    async def test_get_route_shape_returns_404_when_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        response = await client.get(
            "/routes/shape/NONEXISTENT-ROUTE-12345",
            headers=auth["headers"],
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_route_shape_points_have_valid_coordinates(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        response = await client.get("/routes/shape/1012-10", headers=auth["headers"])

        assert response.status_code == 200
        points = response.json()["points"]

        for point in points:
            assert -25 <= point["latitude"] <= -22
            assert -48 <= point["longitude"] <= -45

    @pytest.mark.asyncio
    async def test_get_route_shape_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/routes/shape/1012-10")

        assert response.status_code == 401
