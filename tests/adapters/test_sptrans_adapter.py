import os

import pytest

from src.adapters.external.sptrans_adapter import SpTransAdapter
from src.core.models.bus import BusPosition, BusRoute

skip_if_no_token = pytest.mark.skipif(
    not os.getenv("SPTRANS_API_TOKEN"),
    reason="SPTRANS_API_TOKEN not set - skipping integration test",
)


@skip_if_no_token
@pytest.mark.asyncio
async def test_automatic_authentication() -> None:
    """
    Test that the adapter authenticates automatically when making requests.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    routes: list[BusRoute] = await adapter.search_routes("8075")

    assert "apiCredentials" in adapter.client.cookies, "Cookie de credenciais não foi criado."
    assert len(routes) > 0


@skip_if_no_token
@pytest.mark.asyncio
async def test_search_routes_number() -> None:
    """
    Searches for route number and validates the results.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    bus_routes: list[BusRoute] = await adapter.search_routes("8075")

    assert isinstance(bus_routes, list)
    assert len(bus_routes) > 0, "Nenhuma rota retornada para 8075"

    for bus_route in bus_routes:
        assert isinstance(bus_route.route_id, int), "route_id must be an integer"
        assert bus_route.route_id > 0, "route_id must be positive"
        assert "8075" in bus_route.route.bus_line


@skip_if_no_token
@pytest.mark.asyncio
async def test_search_routes_by_destination() -> None:
    """
    Searches for routes by destination name.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    bus_routes: list[BusRoute] = await adapter.search_routes("Lapa")

    assert isinstance(bus_routes, list)
    assert len(bus_routes) > 0, "Nenhuma rota retornada para Lapa"


@skip_if_no_token
@pytest.mark.asyncio
async def test_get_bus_positions() -> None:
    """
    Fetches real-time positions for route 8075.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    bus_routes: list[BusRoute] = await adapter.search_routes("8075")
    assert len(bus_routes) > 0

    chosen_route: BusRoute = bus_routes[0]
    assert chosen_route.route_id > 0

    positions: list[BusPosition] = await adapter.get_bus_positions(chosen_route.route_id)

    assert positions is not None
    assert isinstance(positions, list)

    if positions:
        pos: BusPosition = positions[0]

        assert isinstance(pos.position.latitude, float | int)
        assert isinstance(pos.position.longitude, float | int)


@skip_if_no_token
@pytest.mark.asyncio
async def test_search_routes_returns_empty_for_unknown() -> None:
    """
    Test that search returns empty list for unknown routes.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    routes: list[BusRoute] = await adapter.search_routes("XYZNONEXISTENT999")

    assert isinstance(routes, list)
    assert len(routes) == 0
