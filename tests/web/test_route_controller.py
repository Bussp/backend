from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.services.route_service import RouteService
from src.main import app  # ajuste o import conforme sua estrutura real
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

    # Tipagem explícita pro mypy/pyright
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


@pytest.mark.asyncio
async def test_positions_endpoint_success(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/positions
    garantindo que:
    - Ele chama RouteService.get_route_details()
    - Ele chama RouteService.get_bus_positions()
    - Ele retorna os dados corretamente
    """

    # ----- Arrange -----
    route_identifier = RouteIdentifier(bus_line="8075", bus_direction=1)
    bus_route = BusRoute(route_id=1234, route=route_identifier)

    position = BusPosition(
        route=route_identifier,
        position=Coordinate(latitude=-23.5, longitude=-46.6),
        time_updated=datetime.now(UTC),
    )

    mock_service.get_route_details.return_value = bus_route  # type: ignore
    mock_service.get_bus_positions.return_value = [position]  # type: ignore

    payload = {"routes": [{"bus_line": "8075", "bus_direction": 1}]}

    # ----- Act -----
    response = client.post("/routes/positions", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()

    # valida formato da resposta
    assert "buses" in data
    assert len(data["buses"]) == 1

    bus = data["buses"][0]

    assert bus["route"]["bus_line"] == "8075"
    assert bus["route"]["bus_direction"] == 1
    assert "position" in bus

    # garante que os métodos do service foram chamados corretamente
    mock_service.get_route_details.assert_awaited_once()
    mock_service.get_bus_positions.assert_awaited_once()


@pytest.mark.asyncio
async def test_positions_endpoint_error_returns_500(
    client: TestClient, mock_service: RouteService
) -> None:
    """
    Testa se o controller retorna 500 caso o service levante exception.
    """

    mock_service.get_route_details.side_effect = RuntimeError("boom")  # type: ignore

    payload = {"routes": [{"bus_line": "8075", "bus_direction": 1}]}

    response = client.post("/routes/positions", json=payload)

    assert response.status_code == 500
    assert "Failed to retrieve bus positions" in response.json()["detail"]
