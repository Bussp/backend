from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.web.schemas import (
    BusPositionsRequest,
    BusRouteSchema,
    BusRoutesDetailsRequest,
    RouteIdentifierSchema,
)

from .conftest import create_user_and_login


class TestRouteDetails:
    @pytest.mark.asyncio
    async def test_get_route_details_returns_successfully(
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
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
            )
        ]

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_route_details",
                new_callable=AsyncMock,
                return_value=mock_bus_routes,
            ),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/details",
                json=request_data.model_dump(),
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
    async def test_get_route_details_with_multiple_lines(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        mock_routes_8000 = [
            BusRoute(
                route_id=12345,
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
            ),
        ]
        mock_routes_9000 = [
            BusRoute(
                route_id=67890,
                route=RouteIdentifier(bus_line="9000", bus_direction=1),
            ),
        ]

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_route_details",
                new_callable=AsyncMock,
                side_effect=[mock_routes_8000, mock_routes_9000],
            ),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    RouteIdentifierSchema(bus_line="9000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/details",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["routes"]) == 2
            route_ids = [r["route_id"] for r in data["routes"]]
            assert 12345 in route_ids
            assert 67890 in route_ids

    @pytest.mark.asyncio
    async def test_get_route_details_returns_empty_for_unknown_line(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_route_details",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="UNKNOWN", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/details",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["routes"] == []

    @pytest.mark.asyncio
    async def test_get_route_details_returns_500_on_api_error(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_route_details",
                new_callable=AsyncMock,
                side_effect=RuntimeError("API unavailable"),
            ),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/details",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 500
            assert "Failed to retrieve route details" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_route_details_with_empty_routes_list(
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
            "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
            new_callable=AsyncMock,
            return_value=True,
        ):
            request_data = BusRoutesDetailsRequest(routes=[])

            response = await client.post(
                "/routes/details",
                json=request_data.model_dump(),
                headers=auth["headers"],
            )

            assert response.status_code == 200
            assert response.json()["routes"] == []

    @pytest.mark.asyncio
    async def test_get_route_details_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        request_data = BusRoutesDetailsRequest(
            routes=[
                RouteIdentifierSchema(bus_line="8000", bus_direction=1),
            ]
        )

        response = await client.post("/routes/details", json=request_data.model_dump())

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
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(UTC),
            ),
            BusPosition(
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.551234, longitude=-46.634567),
                time_updated=datetime.now(UTC),
            ),
        ]

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                return_value=mock_positions,
            ),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteSchema(
                        route_id=12345,
                        route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    ),
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
            assert "route" in first_bus
            assert first_bus["route"]["bus_line"] == "8000"
            assert first_bus["route"]["bus_direction"] == 1
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

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                side_effect=ValueError("Error fetching positions"),
            ),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteSchema(
                        route_id=99999,
                        route=RouteIdentifierSchema(bus_line="123", bus_direction=1),
                    ),
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

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteSchema(
                        route_id=12345,
                        route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    ),
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

        mock_positions_8000 = [
            BusPosition(
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(UTC),
            ),
        ]
        mock_positions_9000 = [
            BusPosition(
                route=RouteIdentifier(bus_line="9000", bus_direction=2),
                position=Coordinate(latitude=-23.560520, longitude=-46.643308),
                time_updated=datetime.now(UTC),
            ),
        ]

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                side_effect=[mock_positions_8000, mock_positions_9000],
            ),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteSchema(
                        route_id=12345,
                        route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    ),
                    BusRouteSchema(
                        route_id=67890,
                        route=RouteIdentifierSchema(bus_line="9000", bus_direction=2),
                    ),
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
            bus_lines = [bus["route"]["bus_line"] for bus in data["buses"]]
            assert "8000" in bus_lines
            assert "9000" in bus_lines

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_500_when_authentication_failure(
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
            "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Authentication failed"),
        ):
            request_data = BusPositionsRequest(
                routes=[
                    BusRouteSchema(
                        route_id=12345,
                        route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    ),
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

        request_data = {
            "routes": [
                {
                    "route_id": 12345,
                    "route": {"bus_line": "8000", "bus_direction": 3},
                }
            ]
        }

        response = await client.post(
            "/routes/positions",
            json=request_data,
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

        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                return_value=[],
            ),
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
                BusRouteSchema(
                    route_id=12345,
                    route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ),
            ]
        )

        response = await client.post("/routes/positions", json=request_data.model_dump())

        assert response.status_code == 401


class TestRouteShapes:
    @pytest.mark.asyncio
    async def test_get_route_shapes_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        request_data = {"routes": [{"bus_line": "1012-10", "bus_direction": 1}]}

        response = await client.post(
            "/routes/shapes",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()

        assert "shapes" in data
        assert len(data["shapes"]) > 0

        first_shape = data["shapes"][0]
        assert "route" in first_shape
        assert first_shape["route"]["bus_line"] == "1012-10"
        assert first_shape["route"]["bus_direction"] == 1
        assert "shape_id" in first_shape
        assert "points" in first_shape
        assert len(first_shape["points"]) > 0

        first_point = first_shape["points"][0]
        assert "latitude" in first_point
        assert "longitude" in first_point
        assert isinstance(first_point["latitude"], float)
        assert isinstance(first_point["longitude"], float)

    @pytest.mark.asyncio
    async def test_get_route_shapes_returns_empty_when_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        request_data = {"routes": [{"bus_line": "NONEXISTENT-ROUTE-12345", "bus_direction": 1}]}

        response = await client.post(
            "/routes/shapes",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["shapes"] == []

    @pytest.mark.asyncio
    async def test_get_route_shapes_multiple_routes(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        request_data = {
            "routes": [
                {"bus_line": "1012-10", "bus_direction": 1},
                {"bus_line": "1012-10", "bus_direction": 2},
            ]
        }

        response = await client.post(
            "/routes/shapes",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()

        # Should return shapes for routes that exist
        assert "shapes" in data

    @pytest.mark.asyncio
    async def test_get_route_shapes_points_have_valid_coordinates(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        request_data = {"routes": [{"bus_line": "1012-10", "bus_direction": 1}]}

        response = await client.post(
            "/routes/shapes",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()

        if data["shapes"]:
            points = data["shapes"][0]["points"]
            for point in points:
                # São Paulo coordinates range
                assert -25 <= point["latitude"] <= -22
                assert -48 <= point["longitude"] <= -45

    @pytest.mark.asyncio
    async def test_get_route_shapes_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        request_data = {"routes": [{"bus_line": "1012-10", "bus_direction": 1}]}

        response = await client.post("/routes/shapes", json=request_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_route_shapes_default_direction(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        # Request without bus_direction (should default to 1)
        request_data = {"routes": [{"bus_line": "1012-10"}]}

        response = await client.post(
            "/routes/shapes",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()

        if data["shapes"]:
            # The returned shape should have direction 1 (default)
            assert data["shapes"][0]["route"]["bus_direction"] == 1
