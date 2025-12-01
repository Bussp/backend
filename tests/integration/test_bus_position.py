from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.core.models.bus import BusPosition, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.web.schemas import BusRoutesDetailsRequest, RouteIdentifierSchema


class TestBusPositions:
    """Test bus position queries."""

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that getting bus positions works when the API returns data."""

        mock_positions = [
            BusPosition(
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(timezone.utc),
            ),
            BusPosition(
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.551234, longitude=-46.634567),
                time_updated=datetime.now(timezone.utc),
            ),
        ]

        # Mock the SpTransAdapter methods
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
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
            )

            assert response.status_code == 200
            data = response.json()

            assert "buses" in data
            assert len(data["buses"]) == 2

            # Verify first bus position structure
            first_bus = data["buses"][0]
            assert "route" in first_bus
            assert first_bus["route"]["bus_line"] == "8000"
            assert first_bus["route"]["bus_direction"] == 1
            assert "position" in first_bus
            assert "latitude" in first_bus["position"]
            assert "longitude" in first_bus["position"]
            assert "time_updated" in first_bus

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_404_when_line_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that getting bus positions returns error when bus line is not found.

        Note: Since the current implementation catches exceptions and returns 500,
        we test that behavior. In a production system, you might want to
        distinguish between "line not found" (404) and "API error" (500).
        """
        # Mock the adapter to simulate line not found
        with (
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.adapters.external.sptrans_adapter.SpTransAdapter.get_bus_positions",
                new_callable=AsyncMock,
                side_effect=ValueError("Line INVALID123 not found"),
            ),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="INVALID123", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
            )

            assert response.status_code == 404
            assert "Failed to retrieve bus positions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_empty_when_no_buses_on_line(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that getting bus positions returns empty list when SPTrans
        returns no buses for a valid line (e.g., no buses currently running).
        """
        # Mock empty response (valid line but no buses currently)
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
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
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
        """Test that querying multiple routes returns positions for all of them."""
        mock_positions = [
            BusPosition(
                route=RouteIdentifier(bus_line="8000", bus_direction=1),
                position=Coordinate(latitude=-23.550520, longitude=-46.633308),
                time_updated=datetime.now(timezone.utc),
            ),
            BusPosition(
                route=RouteIdentifier(bus_line="9000", bus_direction=2),
                position=Coordinate(latitude=-23.560520, longitude=-46.643308),
                time_updated=datetime.now(timezone.utc),
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
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                    RouteIdentifierSchema(bus_line="9000", bus_direction=2),
                ]
            )

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
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
        """Test behavior when SPTrans authentication fails."""
        with patch(
            "src.adapters.external.sptrans_adapter.SpTransAdapter.authenticate",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Authentication failed"),
        ):
            request_data = BusRoutesDetailsRequest(
                routes=[
                    RouteIdentifierSchema(bus_line="8000", bus_direction=1),
                ]
            )

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_422_when_invalid_direction(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that invalid bus direction fails validation."""
        request_data = BusRoutesDetailsRequest(
            routes=[
                RouteIdentifierSchema(bus_line="8000", bus_direction=3),  # Invalid
            ]
        )

        response = await client.post(
            "/routes/positions", json=request_data.model_dump()
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_bus_position_returns_successfully_with_empty_routes_list(
        self,
        client: AsyncClient,
    ) -> None:
        """Test behavior with empty routes list."""
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
            request_data = BusRoutesDetailsRequest(routes=[])

            response = await client.post(
                "/routes/positions", json=request_data.model_dump()
            )

            assert response.status_code == 200
            assert response.json()["buses"] == []
