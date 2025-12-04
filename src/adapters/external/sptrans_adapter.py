"""
SPTrans API adapter - Implementation of BusProviderPort.

This adapter implements the BusProviderPort interface for interacting
with the SPTrans API.
"""

from datetime import datetime

import httpx
from httpx import Response

from src.config import settings

from ...adapters.external.models.LineInfo import LineInfo
from ...adapters.external.models.SPTransPosResp import SPTransPositionsResponse, Vehicle
from ...core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ...core.models.coordinate import Coordinate
from ...core.ports.bus_provider_port import BusProviderPort


class SpTransAdapter(BusProviderPort):
    def __init__(
        self,
        api_token: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the SPTrans adapter.

        Args:
            api_token: API authentication token (optional)
            base_url: Base URL for the SPTrans API (optional)
        """
        # se o parâmetro foi passado, usa ele;
        # senão, usa o valor do settings carregado do .env
        self.api_token = api_token or settings.sptrans_api_token
        self.base_url = base_url or settings.sptrans_base_url

        if not self.api_token:
            raise ValueError(
                "SPTransAdapter: nenhum token fornecido e SPTRANS_API_TOKEN não definido no ambiente/.env."
            )

        self.session_token: str | None = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def authenticate(self) -> bool:
        """
        Authenticate with the SPTrans API.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response: Response = await self.client.post(
                "/Login/Autenticar",
                params={"token": self.api_token},
            )

            if response.status_code == 200 and response.text == "true":
                # marca que autenticou com sucesso
                self.session_token = "authenticated"
                return True

            return False

        except Exception as e:
            exc: Exception = e
            print(f"Authentication failed: {exc}")
            return False

    async def get_bus_positions(self, bus_route: BusRoute) -> list[BusPosition]:
        """
        Get real-time positions for a specific route using SPTrans data.

        Pré-condição:
            O método `authenticate()` deve ter sido chamado com sucesso antes de
            usar este método.

        Args:
            bus_route: BusRoute(route_id=cl, route=RouteIdentifier)

        Returns:
            List of BusPosition objects.
        """
        # Checagem defensiva opcional
        if getattr(self, "session_token", None) != "authenticated":
            raise RuntimeError("SPTrans client not authenticated. Call `authenticate()` first.")

        positions: list[BusPosition] = []

        try:
            line_code: int = bus_route.route_id

            response: Response = await self.client.get(
                "/Posicao/Linha",
                params={"codigoLinha": line_code},
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"SPTrans returned status {response.status_code} for line {bus_route}"
                )

            response_data: SPTransPositionsResponse = response.json()

            vehicles: list[Vehicle] = response_data["vs"]

            for vehicle in vehicles:
                pos: BusPosition = BusPosition(
                    route=bus_route.route,
                    position=Coordinate(
                        latitude=vehicle["py"],
                        longitude=vehicle["px"],
                    ),
                    time_updated=datetime.fromisoformat(vehicle["ta"]),
                )
                positions.append(pos)

        except Exception as e:
            exc: Exception = e
            print(f"Failed to get positions for bus_route {bus_route}: {exc}")

        return positions

    async def get_route_details(self, route: RouteIdentifier) -> list[BusRoute]:
        """
        Resolve a logical bus line (bus_line) into all SPTrans BusRoute entries using
        the `/Linha/Buscar` endpoint.

        Args:
            route (RouteIdentifier): Logical bus line (ex: "8000")

        Returns:
            list[BusRoute]: Todas as variantes da linha retornadas pela SPTrans.

        Raises:
            RuntimeError: Se a requisição falhar, vier vazia ou inválida.
        """

        # Verifica se está autenticado
        if getattr(self, "session_token", None) != "authenticated":
            raise RuntimeError("SPTrans client not authenticated. Call `authenticate()` first.")

        try:
            response: Response = await self.client.get(
                "/Linha/Buscar",
                params={"termosBusca": route.bus_line},
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"SPTrans returned status {response.status_code} for line search."
                )

            data: list[LineInfo] = response.json()

            if not isinstance(data, list) or len(data) == 0:
                raise RuntimeError(f"No SPTrans line found for line={route.bus_line}")

            bus_routes: list[BusRoute] = []

            for item in data:
                # Validate based on TypedDict keys
                if "cl" not in item or "lt" not in item:
                    continue  # Skip invalid entries

                line_code = item["cl"]
                line_text = item["lt"]
                line_dir = item["sl"]

                bus_routes.append(
                    BusRoute(
                        route_id=line_code,
                        route=RouteIdentifier(bus_line=line_text, bus_direction=line_dir),
                    )
                )

            if not bus_routes:
                raise RuntimeError(
                    f"Invalid SPTrans response for line={route.bus_line}: "
                    "missing required fields"
                )

            return bus_routes

        except Exception as e:
            raise RuntimeError(f"Failed to resolve route details for {route}: {e}") from e
