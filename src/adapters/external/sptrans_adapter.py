"""
SPTrans API adapter - Implementation of BusProviderPort.

This adapter implements the BusProviderPort interface for interacting
with the SPTrans API.
"""

from datetime import datetime

import httpx

from ...core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ...core.models.coordinate import Coordinate
from ...core.ports.bus_provider_port import BusProviderPort


class SpTransAdapter(BusProviderPort):
    """
    HTTP client implementation of the BusProviderPort interface.

    This adapter communicates with the SPTrans API to retrieve
    real-time bus information.
    """

    def __init__(self, api_token: str, base_url: str = "http://api.olhovivo.sptrans.com.br/v2.1"):
        """
        Initialize the SPTrans adapter.

        Args:
            api_token: API authentication token
            base_url: Base URL for the SPTrans API
        """
        self.api_token = api_token
        self.base_url = base_url
        self.session_token: str | None = None
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def authenticate(self) -> bool:
        """
        Authenticate with the SPTrans API.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response = await self.client.post("/Login/Autenticar", params={"token": self.api_token})

            if response.status_code == 200 and response.text == "true":
                # Store cookies for subsequent requests
                self.session_token = "authenticated"
                return True

            return False

        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    async def get_bus_positions(self, routes: list[RouteIdentifier]) -> list[BusPosition]:
        """
        Get real-time positions for specified bus routes.

        Args:
            routes: List of route identifiers to query

        Returns:
            List of current bus positions

        Raises:
            Exception: If API call fails
        """
        if not self.session_token:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        positions: list[BusPosition] = []

        # For each route, query the API
        for route in routes:
            try:
                # SPTrans API expects: /Posicao/Linha?codigoLinha={line_code}
                # In a real implementation, you'd need to map bus_line to line code
                response = await self.client.get(
                    "/Posicao/Linha", params={"codigoLinha": route.bus_line}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Parse response according to SPTrans API format
                    # hr: current time, vs: vehicles
                    vehicles = data.get("vs", [])

                    for vehicle in vehicles:
                        # Convert from SPTrans format to domain model
                        position = BusPosition(
                            route=route,
                            position=Coordinate(
                                latitude=vehicle["py"] / 1_000_000,  # SPTrans uses lat * 10^6
                                longitude=vehicle["px"] / 1_000_000,
                            ),
                            time_updated=(
                                datetime.fromisoformat(vehicle["ta"])
                                if isinstance(vehicle["ta"], str)
                                else vehicle["ta"]
                            ),
                        )
                        positions.append(position)

            except Exception as e:
                print(f"Failed to get positions for route {route.bus_line}: {e}")
                continue

        return positions

    async def get_route_details(self, route: RouteIdentifier) -> BusRoute:
        """
        Get detailed information about a route.

        Args:
            route: Route identifier

        Returns:
            Bus route details

        Raises:
            Exception: If route not found or API fails
        """
        if not self.session_token:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # SPTrans API: /Linha/Buscar?termosBusca={search_term}
            response = await self.client.get(
                "/Linha/Buscar", params={"termosBusca": route.bus_line}
            )

            if response.status_code == 200:
                data = response.json()

                # Assuming first match is the desired route
                if data and len(data) > 0:
                    route_data = data[0]
                    return BusRoute(
                        route_id=route_data["cl"],  # cl: route code
                        route=route,
                    )

            raise ValueError(f"Route {route.bus_line} not found")

        except Exception as e:
            raise RuntimeError(f"Failed to get route details: {e}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
