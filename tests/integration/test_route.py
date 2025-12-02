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


class TestRouteDetails:
    @pytest.mark.asyncio
    async def test_get_route_details_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/details", json=request_data.model_dump())

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

            response = await client.post("/routes/details", json=request_data.model_dump())

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

            response = await client.post("/routes/details", json=request_data.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert data["routes"] == []

    @pytest.mark.asyncio
    async def test_get_route_details_returns_500_on_api_error(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/details", json=request_data.model_dump())

            assert response.status_code == 500
            assert "Failed to retrieve route details" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_route_details_with_empty_routes_list(
        self,
        client: AsyncClient,
    ) -> None:
        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
            new_callable=AsyncMock,
            return_value=True,
        ):
            request_data = BusRoutesDetailsRequest(routes=[])

            response = await client.post("/routes/details", json=request_data.model_dump())

            assert response.status_code == 200
            assert response.json()["routes"] == []


class TestBusPositions:
    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/positions", json=request_data.model_dump())

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

            response = await client.post("/routes/positions", json=request_data.model_dump())

            assert response.status_code == 500
            assert "Failed to retrieve bus positions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_empty_when_no_buses_on_line(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/positions", json=request_data.model_dump())

            assert response.status_code == 200
            data = response.json()

            assert "buses" in data
            assert len(data["buses"]) == 0

    @pytest.mark.asyncio
    async def test_get_bus_position_works_with_multiple_routes(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/positions", json=request_data.model_dump())

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

            response = await client.post("/routes/positions", json=request_data.model_dump())

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_422_when_invalid_data(
        self,
        client: AsyncClient,
    ) -> None:
        request_data = {
            "routes": [
                {
                    "route_id": 12345,
                    "route": {"bus_line": "8000", "bus_direction": 3},
                }
            ]
        }

        response = await client.post("/routes/positions", json=request_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully_with_empty_routes_list(
        self,
        client: AsyncClient,
    ) -> None:
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

            response = await client.post("/routes/positions", json=request_data.model_dump())

            assert response.status_code == 200
            assert response.json()["buses"] == []


class TestRouteShape:
    """Tests for GET /routes/shape/{route_id} endpoint.

    These tests use the actual GTFS database (gtfs.db) since
    GTFSRepositoryAdapter is a local database adapter, not an external service.
    """

    @pytest.mark.asyncio
    async def test_get_route_shape_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/routes/shape/1012-10")

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
        response = await client.get("/routes/shape/NONEXISTENT-ROUTE-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_route_shape_points_have_valid_coordinates(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/routes/shape/1012-10")

        assert response.status_code == 200
        points = response.json()["points"]

        # São Paulo approximate bounding box
        for point in points:
            # Latitude should be around -23 to -24 for São Paulo
            assert -25 <= point["latitude"] <= -22
            # Longitude should be around -46 to -47 for São Paulo
            assert -48 <= point["longitude"] <= -45
