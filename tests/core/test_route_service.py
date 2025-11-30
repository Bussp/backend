from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.ports.bus_provider_port import BusProviderPort
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
    raw_provider.get_bus_positions.return_value = expected_positions  # type: ignore[assignment]

    service: RouteService = RouteService(bus_provider=bus_provider)

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
    raw_provider.get_route_details.return_value = expected_routes  # type: ignore[assignment]

    service: RouteService = RouteService(bus_provider=bus_provider)

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

    service: RouteService = RouteService(bus_provider=bus_provider)

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

    service: RouteService = RouteService(bus_provider=bus_provider)

    # Act / Assert
    with pytest.raises(RuntimeError, match="auth failed"):
        await service.get_route_details(route_identifier)

    raw_provider.authenticate.assert_awaited_once()
    raw_provider.get_route_details.assert_not_awaited()
