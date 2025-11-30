from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.services.route_service import RouteService
from src.main import app
from src.web.controllers.route_controller import get_route_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_service() -> RouteService:
    """
    Cria um mock fortemente tipado do RouteService,
    mas com métodos assíncronos (AsyncMock).
    """
    service = AsyncMock(spec=RouteService)

    typed_service: RouteService = service  # type: ignore[assignment]
    return typed_service


@pytest.fixture(autouse=True)
def override_dependency(mock_service: RouteService) -> None:
    """
    Override da dependência get_route_service para usar o mock.
    """
    app.dependency_overrides[get_route_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()


# =========================
# /routes/details
# =========================


@pytest.mark.asyncio
async def test_details_endpoint_success(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/details garantindo que:
    - Ele chama RouteService.get_route_details()
    - Ele retorna uma lista achatada de rotas
    """

    # ----- Arrange -----
    # domínio
    route_identifier = RouteIdentifier(bus_line="8075", bus_direction=1)
    bus_route_1 = BusRoute(route_id=2044, route=route_identifier)
    bus_route_2 = BusRoute(route_id=34812, route=route_identifier)

    # get_route_details agora retorna list[BusRoute]
    mock_service.get_route_details.return_value = [bus_route_1, bus_route_2]  # type: ignore[assignment]

    payload = {
        "routes": [
            {"bus_line": "8075"},
        ]
    }

    # ----- Act -----
    response = client.post("/routes/details", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()

    assert "routes" in data
    assert len(data["routes"]) == 2

    routes = data["routes"]

    assert routes[0]["route_id"] == 2044
    assert routes[0]["route"]["bus_line"] == "8075"

    assert routes[1]["route_id"] == 34812
    assert routes[1]["route"]["bus_line"] == "8075"

    # garante que o service foi chamado uma vez
    mock_service.get_route_details.assert_awaited_once()
    called_arg = mock_service.get_route_details.await_args.args[0]
    assert isinstance(called_arg, RouteIdentifier)
    assert called_arg.bus_line == "8075"
    # direção padrão que estamos usando
    assert called_arg.bus_direction == 1


@pytest.mark.asyncio
async def test_details_endpoint_error_returns_500(
    client: TestClient, mock_service: RouteService
) -> None:
    """
    Testa se o controller retorna 500 caso o service levante exception
    em /routes/details.
    """

    mock_service.get_route_details.side_effect = RuntimeError("boom")  # type: ignore[assignment]

    payload = {"routes": [{"bus_line": "8075"}]}

    response = client.post("/routes/details", json=payload)

    assert response.status_code == 500
    body = response.json()
    assert "Failed to retrieve route details" in body["detail"]


# =========================
# /routes/positions
# =========================


@pytest.mark.asyncio
async def test_positions_endpoint_success(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/positions garantindo que:
    - Ele chama RouteService.get_bus_positions()
    - Ele retorna os dados de posição corretamente
    """

    # ----- Arrange -----
    route_identifier = RouteIdentifier(bus_line="8075", bus_direction=1)

    position = BusPosition(
        route=route_identifier,
        position=Coordinate(latitude=-23.5, longitude=-46.6),
        time_updated=datetime.now(UTC),
    )

    mock_service.get_bus_positions.return_value = [position]  # type: ignore[assignment]

    payload = {
        "routes": [
            {
                "route_id": 2044,
                "route": {"bus_line": "8075"},
            }
        ]
    }

    # ----- Act -----
    response = client.post("/routes/positions", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()

    assert "buses" in data
    assert len(data["buses"]) == 1

    bus = data["buses"][0]

    assert bus["route"]["bus_line"] == "8075"
    assert "position" in bus
    assert "latitude" in bus["position"]
    assert "longitude" in bus["position"]
    assert "time_updated" in bus

    mock_service.get_bus_positions.assert_awaited_once()
    called_arg = mock_service.get_bus_positions.await_args.args[0]
    assert isinstance(called_arg, BusRoute)
    assert called_arg.route.bus_line == "8075"
    assert called_arg.route.bus_direction == 1
    assert called_arg.route_id == 2044


@pytest.mark.asyncio
async def test_positions_endpoint_error_returns_500(
    client: TestClient, mock_service: RouteService
) -> None:
    """
    Testa se o controller retorna 500 caso o service levante exception
    em /routes/positions.
    """

    mock_service.get_bus_positions.side_effect = RuntimeError("boom")  # type: ignore[assignment]

    payload = {
        "routes": [
            {
                "route_id": 2044,
                "route": {"bus_line": "8075"},
            }
        ]
    }

    response = client.post("/routes/positions", json=payload)

    assert response.status_code == 500
    body = response.json()
    assert "Failed to retrieve bus positions" in body["detail"]
