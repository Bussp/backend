import pytest

from src.adapters.external.sptrans_adapter import SpTransAdapter
from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier


@pytest.mark.asyncio
async def test_authentication() -> None:
    """
    Real authentication test against SPTrans.
    Requires SPTRANS_API_TOKEN to be configured.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    ok: bool = await adapter.authenticate()

    print("Cookies recebidos:", adapter.client.cookies)

    assert ok is True, "A autenticação real falhou. Verifique seu TOKEN."
    assert "apiCredentials" in adapter.client.cookies, (
        "Cookie de credenciais não foi criado."
    )


@pytest.mark.asyncio
async def test_get_route_details_8075_direction_1() -> None:
    """
    Integration test: resolves the internal SPTrans 'codigoLinha' (cl)
    for route 8075-10, direction 1 using get_route_details().
    """
    adapter: SpTransAdapter = SpTransAdapter()

    await adapter.authenticate()

    # RouteIdentifier for 8075-10 direction 1
    route: RouteIdentifier = RouteIdentifier(bus_line="8075", bus_direction=1)

    # Fetch BusRoute
    bus_route: BusRoute = await adapter.get_route_details(route)

    print("Retrieved BusRoute:", bus_route)

    # Validate result
    assert isinstance(bus_route.route_id, int), "route_id must be an integer"
    assert bus_route.route_id > 0, "route_id must be positive"
    assert bus_route.route == route


@pytest.mark.asyncio
async def test_get_bus_positions_8075_direction_1() -> None:
    """
    Integration test: fetches real-time positions for route 8075-10, direction 1,
    using get_route_details() + get_bus_positions(), no mocks.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    await adapter.authenticate()

    route: RouteIdentifier = RouteIdentifier(bus_line="8075", bus_direction=1)

    # Step 1: resolve SPTrans internal code
    bus_route: BusRoute = await adapter.get_route_details(route)
    assert bus_route.route_id > 0

    # Step 2: fetch positions using BusRoute
    positions: list[BusPosition] = await adapter.get_bus_positions([route])

    assert positions is not None
    assert isinstance(positions, list)

    # If there are vehicles, validate fields
    if positions:
        pos: BusPosition = positions[0]

        # Route info should match what we requested
        assert pos.route.bus_line == "8075"
        assert pos.route.bus_direction == 1

        # Coordinate validation (Ruff UP038: use union instead of tuple)
        assert isinstance(pos.position.latitude, float | int)
        assert isinstance(pos.position.longitude, float | int)


@pytest.mark.asyncio
async def test_get_route_details_without_authentication():
    adapter: SpTransAdapter = SpTransAdapter(api_token="INVALID")

    route = RouteIdentifier(bus_line="8075", bus_direction=1)

    with pytest.raises(RuntimeError, match="not authenticated"):
        await adapter.get_route_details(route)

@pytest.mark.asyncio
async def test_get_bus_positions_without_authentication():
    adapter: SpTransAdapter = SpTransAdapter()

    bus_route = BusRoute(
        route_id=8075,
        route=RouteIdentifier(bus_line="8075", bus_direction=1)
    )

    with pytest.raises(RuntimeError, match="not authenticated"):
        await adapter.get_bus_positions(bus_route)
