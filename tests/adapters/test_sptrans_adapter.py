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
    assert "apiCredentials" in adapter.client.cookies, "Cookie de credenciais não foi criado."


@pytest.mark.asyncio
async def test_get_route_details_8075_direction_1() -> None:
    """
    Integration test: resolves the internal SPTrans 'codigoLinha' (cl)
    for route 8075 using get_route_details(), which now returns a list
    of BusRoute entries (diferentes sentidos/variações).
    """
    adapter: SpTransAdapter = SpTransAdapter()

    await adapter.authenticate()

    # RouteIdentifier para linha 8075 (direção ainda existe no domínio)
    route: RouteIdentifier = RouteIdentifier(bus_line="8075", bus_direction=1)

    # Agora get_route_details retorna list[BusRoute]
    bus_routes: list[BusRoute] = await adapter.get_route_details(route)

    print("Retrieved BusRoutes:", bus_routes)

    # Validate result
    assert isinstance(bus_routes, list)
    assert len(bus_routes) > 0, "Nenhuma rota retornada para 8075"

    for bus_route in bus_routes:
        assert isinstance(bus_route.route_id, int), "route_id must be an integer"
        assert bus_route.route_id > 0, "route_id must be positive"
        # a linha deve bater com o que pedimos
        assert bus_route.route.bus_line == "8075"


@pytest.mark.asyncio
async def test_get_bus_positions_8075_direction_1() -> None:
    """
    Integration test: fetches real-time positions for one concrete route
    of line 8075 (direction 1, se disponível), usando
    get_route_details() + get_bus_positions(), sem mocks.
    """
    adapter: SpTransAdapter = SpTransAdapter()

    await adapter.authenticate()

    route: RouteIdentifier = RouteIdentifier(bus_line="8075", bus_direction=1)

    # Step 1: resolve SPTrans internal codes (list[BusRoute])
    bus_routes: list[BusRoute] = await adapter.get_route_details(route)
    assert len(bus_routes) > 0

    # escolhe uma rota com direction 1, se existir; senão, pega a primeira
    chosen_route: BusRoute = next(
        (br for br in bus_routes if getattr(br.route, "bus_direction", None) == 1),
        bus_routes[0],
    )

    assert chosen_route.route_id > 0

    # Step 2: fetch positions usando BusRoute concreto
    positions: list[BusPosition] = await adapter.get_bus_positions(chosen_route)

    assert positions is not None
    assert isinstance(positions, list)

    if positions:
        pos: BusPosition = positions[0]

        # Route info should match what we requested (mesma linha)
        assert pos.route.bus_line == "8075"

        # se tiver direction em BusPosition.route, valida também
        if hasattr(pos.route, "bus_direction"):
            assert pos.route.bus_direction in (1, 2)

        # Coordenadas
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
        route=RouteIdentifier(bus_line="8075", bus_direction=1),
    )

    with pytest.raises(RuntimeError, match="not authenticated"):
        await adapter.get_bus_positions(bus_route)
