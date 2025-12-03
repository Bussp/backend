"""
SPTrans API adapter - Implementation of BusProviderPort.

This adapter implements the BusProviderPort interface for interacting
with the SPTrans API.
"""

import httpx
from httpx import Response

from src.config import settings

from ...core.models.bus import BusPosition, BusRoute
from ...core.ports.bus_provider_port import BusProviderPort
from .sptrans_mappers import (
    map_positions_response_to_bus_positions,
    map_search_response_to_bus_route_list,
)
from .sptrans_schemas import SPTransLineSearchResponse, SPTransPositionsResponse


class SpTransAdapter(BusProviderPort):
    def __init__(
        self,
        api_token: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the SPTrans adapter.

        Args:
            api_token: API authentication token (optional, defaults to settings)
            base_url: Base URL for the SPTrans API (optional, defaults to settings)

        Raises:
            ValueError: If no API token is provided or configured.
        """
        self.api_token = api_token or settings.sptrans_api_token
        self.base_url = base_url or settings.sptrans_base_url

        if not self.api_token:
            raise ValueError(
                "SPTransAdapter: nenhum token fornecido e SPTRANS_API_TOKEN não definido no ambiente/.env."
            )

        self._authenticated: bool = False
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def _ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated, authenticating if necessary.

        Raises:
            RuntimeError: If authentication fails.
        """
        if not self._authenticated:
            success = await self._authenticate()
            if not success:
                raise RuntimeError("SPTrans authentication failed")

    async def _authenticate(self) -> bool:
        """
        Authenticate with the SPTrans API.

        Returns:
            True if authentication successful, False otherwise.
        """
        try:
            response: Response = await self.client.post(
                "/Login/Autenticar",
                params={"token": self.api_token},
            )

            if response.status_code == 200 and response.text == "true":
                self._authenticated = True
                return True

            return False

        except Exception:
            return False

    def _is_unauthorized_response(self, response: Response) -> bool:
        """
        Check if response indicates authentication is required.

        Args:
            response: HTTP response to check.

        Returns:
            True if response indicates unauthorized access.
        """
        if response.status_code != 401:
            return False

        try:
            data = response.json()
            return "Authorization has been denied" in data.get("Message", "")
        except Exception:
            return False

    async def _request_with_auth_retry(
        self,
        method: str,
        url: str,
        params: dict[str, str | int] | None = None,
    ) -> Response:
        """
        Make an HTTP request with automatic authentication retry on 401.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL path.
            params: Query parameters for the request.

        Returns:
            HTTP response.

        Raises:
            RuntimeError: If authentication fails after retry.
        """
        await self._ensure_authenticated()

        response = await self.client.request(method, url, params=params)

        if self._is_unauthorized_response(response):
            self._authenticated = False
            await self._ensure_authenticated()
            response = await self.client.request(method, url, params=params)

            if self._is_unauthorized_response(response):
                raise RuntimeError("SPTrans authentication failed after retry")

        return response

    async def get_bus_positions(self, routes: list[BusRoute]) -> list[BusPosition]:
        """
        Get real-time positions for specified routes.

        Args:
            routes: List of BusRoute objects containing route info.

        Returns:
            List of BusPosition objects with route identifier and coordinates.
        """
        positions: list[BusPosition] = []

        for bus_route in routes:
            response = await self._request_with_auth_retry(
                "GET",
                "/Posicao/Linha",
                params={"codigoLinha": bus_route.route_id},
            )

            if response.status_code != 200:
                continue

            response_data = SPTransPositionsResponse.model_validate(response.json())
            route_positions = map_positions_response_to_bus_positions(
                response_data,
                bus_route.route,
            )
            positions.extend(route_positions)

        return positions

    async def search_routes(self, query: str) -> list[BusRoute]:
        """
        Search for bus routes matching a query string.

        Args:
            query: Search term (e.g., "809" or "Vila Nova Conceição").

        Returns:
            List of matching BusRoute objects.
        """
        response = await self._request_with_auth_retry(
            "GET",
            "/Linha/Buscar",
            params={"termosBusca": query},
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"SPTrans returned status {response.status_code} for search."
            )

        response_data = SPTransLineSearchResponse.model_validate(response.json())
        bus_routes: list[BusRoute] = map_search_response_to_bus_route_list(response_data)
        return bus_routes
