"""Route service - Business logic for route and bus position queries."""

from ..models.bus import BusPosition, BusRoute
from ..models.route_shape import RouteShape
from ..ports.bus_provider_port import BusProviderPort
from ..ports.gtfs_repository import GTFSRepositoryPort


class RouteService:
    """
    Service containing business logic for route and bus position operations.

    This service interfaces with external bus tracking APIs to provide
    real-time bus information and GTFS data for route shapes.
    """

    def __init__(
        self, bus_provider: BusProviderPort, gtfs_repository: GTFSRepositoryPort
    ):
        """
        Initialize the route service.

        Args:
            bus_provider: Implementation of BusProviderPort.
            gtfs_repository: Implementation of GTFSRepositoryPort.
        """
        self.bus_provider = bus_provider
        self.gtfs_repository = gtfs_repository

    async def get_bus_positions(self, routes: list[BusRoute]) -> list[BusPosition]:
        """
        Get current positions for specified routes.

        Args:
            routes: List of BusRoute objects containing route info.

        Returns:
            List of current bus positions.

        Raises:
            RuntimeError: If API request fails.
        """
        return await self.bus_provider.get_bus_positions(routes)

    async def search_routes(self, query: str) -> list[BusRoute]:
        """
        Search for bus routes matching a query string.

        Args:
            query: Search term (e.g., "809" or "Vila Nova Conceição").

        Returns:
            List of matching bus routes.

        Raises:
            RuntimeError: If API request fails.
        """
        return await self.bus_provider.search_routes(query)

    def get_route_shape(self, bus_line: str) -> RouteShape | None:
        """
        Get the geographic shape coordinates of a route from GTFS data.

        Args:
            bus_line: Bus line identifier (e.g., "1012-10").

        Returns:
            RouteShape with ordered coordinates, or None if route not found.
        """
        return self.gtfs_repository.get_route_shape(bus_line)
