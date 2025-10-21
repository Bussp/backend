"""Route service - Business logic for route and bus position queries."""

from ..models.bus import BusPosition, BusRoute, RouteIdentifier
from ..ports.bus_provider_port import BusProviderPort


class RouteService:
    """
    Service containing business logic for route and bus position operations.

    This service interfaces with external bus tracking APIs to provide
    real-time bus information.
    """

    def __init__(self, bus_provider: BusProviderPort):
        """
        Initialize the route service.

        Args:
            bus_provider: Implementation of BusProviderPort
        """
        self.bus_provider = bus_provider

    async def get_bus_positions(self, routes: list[RouteIdentifier]) -> list[BusPosition]:
        """
        Get current positions for specified bus routes.

        Args:
            routes: List of route identifiers to query

        Returns:
            List of current bus positions

        Raises:
            Exception: If API authentication fails or request fails
        """
        # Ensure we're authenticated
        await self.bus_provider.authenticate()

        # Get positions
        return await self.bus_provider.get_bus_positions(routes)

    async def get_route_details(self, route: RouteIdentifier) -> BusRoute:
        """
        Get detailed information about a route.

        Args:
            route: Route identifier

        Returns:
            Route details

        Raises:
            Exception: If route not found or API fails
        """
        await self.bus_provider.authenticate()
        return await self.bus_provider.get_route_details(route)
