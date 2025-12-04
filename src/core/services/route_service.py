"""Route service - Business logic for route and bus position queries."""

from ..models.bus import BusPosition, BusRoute, RouteIdentifier
from ..models.route_shape import RouteShape
from ..ports.bus_provider_port import BusProviderPort
from ..ports.gtfs_repository import GTFSRepositoryPort


class RouteService:
    """
    Service containing business logic for route and bus position operations.

    This service interfaces with external bus tracking APIs to provide
    real-time bus information and GTFS data for route shapes.
    """

    def __init__(self, bus_provider: BusProviderPort, gtfs_repository: GTFSRepositoryPort):
        """
        Initialize the route service.

        Args:
            bus_provider: Implementation of BusProviderPort.
            gtfs_repository: Implementation of GTFSRepositoryPort.
        """
        self.bus_provider = bus_provider
        self.gtfs_repository = gtfs_repository

    async def get_bus_positions(
        self,
        route_ids: list[int],
    ) -> list[BusPosition]:
        """
        Get current positions for specified routes.

        Args:
            route_ids: List of provider-specific route IDs.

        Returns:
            List of current bus positions.

        Raises:
            RuntimeError: If API request fails.
        """
        positions: list[BusPosition] = []
        for route_id in route_ids:
            route_positions: list[BusPosition] = await self.bus_provider.get_bus_positions(route_id)
            positions.extend(route_positions)
        return positions

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

    def get_route_shapes(self, routes: list[RouteIdentifier]) -> list[RouteShape]:
        """
        Get the geographic shape coordinates for multiple routes from GTFS data.

        Args:
            routes: List of route identifiers with bus_line and direction

        Returns:
            List of RouteShapes with ordered coordinates (excludes routes not found)
        """
        shapes: list[RouteShape] = []
        for route in routes:
            shape = self.gtfs_repository.get_route_shape(route)
            if shape is not None:
                shapes.append(shape)
        return shapes
