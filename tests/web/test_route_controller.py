from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from src.core.models.bus import BusPosition, BusRoute, RouteIdentifier
from src.core.models.coordinate import Coordinate
from src.core.models.route_shape import RouteShape, RouteShapePoint
from src.core.models.user import User
from src.core.services.route_service import RouteService
from src.main import app
from src.web.auth import get_current_user
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
    typed_service: RouteService = service
    typed_service.get_route_details = AsyncMock()  # type: ignore[method-assign]
    typed_service.get_bus_positions = AsyncMock()  # type: ignore[method-assign]
    typed_service.get_route_shape = Mock()  # type: ignore[method-assign]
    typed_service.get_route_shapes = Mock()  # type: ignore[method-assign]
    return typed_service


@pytest.fixture
def mock_current_user() -> User:
    return User(name="Test User", email="test@example.com", score=0)


@pytest.fixture(autouse=True)
def override_dependency(
    mock_service: RouteService, mock_current_user: User
) -> Generator[None, None, None]:
    app.dependency_overrides[get_route_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
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
    mock_service.get_route_details.return_value = [bus_route_1, bus_route_2]  # type: ignore[attr-defined]

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
    mock_service.get_route_details.assert_awaited_once()  # type: ignore[attr-defined]
    called_arg = mock_service.get_route_details.await_args.args[0]  # type: ignore[attr-defined]
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

    mock_service.get_route_details.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

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

    mock_service.get_bus_positions.return_value = [position]  # type: ignore[attr-defined]

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

    mock_service.get_bus_positions.assert_awaited_once()  # type: ignore[attr-defined]
    called_arg = mock_service.get_bus_positions.await_args.args[0]  # type: ignore[attr-defined]
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

    mock_service.get_bus_positions.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

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


# =========================
# /routes/shapes
# =========================


@pytest.mark.asyncio
async def test_shapes_endpoint_success(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/shapes garantindo que:
    - Ele chama RouteService.get_route_shapes()
    - Ele retorna uma lista de shapes
    """

    # ----- Arrange -----
    route1 = RouteIdentifier(bus_line="8075", bus_direction=1)
    route2 = RouteIdentifier(bus_line="8075", bus_direction=2)

    shape1 = RouteShape(
        route=route1,
        shape_id="shape_8075_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            ),
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5510, longitude=-46.6340),
                sequence=2,
                distance_traveled=10.5,
            ),
        ],
    )

    shape2 = RouteShape(
        route=route2,
        shape_id="shape_8075_2",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5515, longitude=-46.6345),
                sequence=1,
                distance_traveled=0.0,
            ),
        ],
    )

    mock_service.get_route_shapes.return_value = [shape1, shape2]  # type: ignore[attr-defined]

    payload = {
        "routes": [
            {"bus_line": "8075", "bus_direction": 1},
            {"bus_line": "8075", "bus_direction": 2},
        ]
    }

    # ----- Act -----
    response = client.post("/routes/shapes", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()

    assert "shapes" in data
    assert len(data["shapes"]) == 2

    # First shape
    assert data["shapes"][0]["route"]["bus_line"] == "8075"
    assert data["shapes"][0]["route"]["bus_direction"] == 1
    assert data["shapes"][0]["shape_id"] == "shape_8075_1"
    assert len(data["shapes"][0]["points"]) == 2

    # Second shape
    assert data["shapes"][1]["route"]["bus_line"] == "8075"
    assert data["shapes"][1]["route"]["bus_direction"] == 2
    assert data["shapes"][1]["shape_id"] == "shape_8075_2"
    assert len(data["shapes"][1]["points"]) == 1

    # Verify service was called correctly
    mock_service.get_route_shapes.assert_called_once()  # type: ignore[attr-defined]
    called_args = mock_service.get_route_shapes.call_args.args[0]  # type: ignore[attr-defined]
    assert len(called_args) == 2
    assert called_args[0].bus_line == "8075"
    assert called_args[0].bus_direction == 1
    assert called_args[1].bus_line == "8075"
    assert called_args[1].bus_direction == 2


@pytest.mark.asyncio
async def test_shapes_endpoint_single_route(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/shapes com uma única rota.
    """

    # ----- Arrange -----
    route = RouteIdentifier(bus_line="1012", bus_direction=1)

    shape = RouteShape(
        route=route,
        shape_id="shape_1012_1",
        points=[
            RouteShapePoint(
                coordinate=Coordinate(latitude=-23.5505, longitude=-46.6333),
                sequence=1,
                distance_traveled=0.0,
            ),
        ],
    )

    mock_service.get_route_shapes.return_value = [shape]  # type: ignore[attr-defined]

    payload = {"routes": [{"bus_line": "1012", "bus_direction": 1}]}

    # ----- Act -----
    response = client.post("/routes/shapes", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()

    assert len(data["shapes"]) == 1
    assert data["shapes"][0]["route"]["bus_line"] == "1012"
    assert data["shapes"][0]["route"]["bus_direction"] == 1


@pytest.mark.asyncio
async def test_shapes_endpoint_empty_result(client: TestClient, mock_service: RouteService) -> None:
    """
    Testa o endpoint POST /routes/shapes quando nenhuma rota é encontrada.
    """

    mock_service.get_route_shapes.return_value = []  # type: ignore[attr-defined]

    payload = {"routes": [{"bus_line": "nonexistent", "bus_direction": 1}]}

    # ----- Act -----
    response = client.post("/routes/shapes", json=payload)

    # ----- Assert -----
    assert response.status_code == 200
    data = response.json()
    assert data["shapes"] == []


@pytest.mark.asyncio
async def test_shapes_endpoint_error_returns_500(
    client: TestClient, mock_service: RouteService
) -> None:
    """
    Testa se o controller retorna 500 caso o service levante exception
    em /routes/shapes.
    """

    mock_service.get_route_shapes.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

    payload = {"routes": [{"bus_line": "8075", "bus_direction": 1}]}

    response = client.post("/routes/shapes", json=payload)

    assert response.status_code == 500
    body = response.json()
    assert "Failed to retrieve route shapes" in body["detail"]
