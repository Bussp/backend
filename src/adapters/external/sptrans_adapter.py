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
                        latitude=vehicle["py"] / 1_000_000,
                        longitude=vehicle["px"] / 1_000_000,
                    ),
                    time_updated=datetime.fromisoformat(vehicle["ta"]),
                )
                positions.append(pos)

        except Exception as e:
            exc: Exception = e
            print(f"Failed to get positions for bus_route {bus_route}: {exc}")

        return positions

    async def get_route_details(self, route: RouteIdentifier) -> BusRoute:
        """
        Resolve a RouteIdentifier into a BusRoute by fetching the internal SPTrans
        'codigoLinha' (cl) using the `/Linha/BuscarLinhaSentido` endpoint.

        Pré-condição:
            O método `authenticate()` deve ter sido chamado com sucesso antes de
            usar este método.

        Args:
            route (RouteIdentifier): The logical bus route (line + direction)
                used to query SPTrans.

        Returns:
            BusRoute: A domain object containing the internal SPTrans line code (cl)
            and the original RouteIdentifier.

        Raises:
            RuntimeError: If the SPTrans API returns an error status code,
                if the route cannot be found, or if the provider returns an invalid
                response format.
        """
        # Checagem defensiva opcional
        if getattr(self, "session_token", None) != "authenticated":
            raise RuntimeError("SPTrans client not authenticated. Call `authenticate()` first.")

        try:
            response: Response = await self.client.get(
                "/Linha/BuscarLinhaSentido",
                params={
                    "termosBusca": route.bus_line,
                    "sentido": route.bus_direction,
                },
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"SPTrans returned status {response.status_code} for line search."
                )

            data: list[LineInfo] = response.json()

            if not isinstance(data, list) or len(data) == 0:
                raise RuntimeError(
                    f"No SPTrans line found for line={route.bus_line}, "
                    f"direction={route.bus_direction}"
                )

            line_info: LineInfo = data[0]

            if "cl" not in line_info:
                raise RuntimeError("Invalid SPTrans response: missing 'cl' field")

            bus_route: BusRoute = BusRoute(
                route_id=line_info["cl"],
                route=route,
            )

            return bus_route

        except Exception as e:
            exc: Exception = e
            raise RuntimeError(f"Failed to resolve route details for {route}: {exc}") from exc

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
