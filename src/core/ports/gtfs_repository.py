"""GTFS repository port."""

from abc import ABC, abstractmethod

from ..models.bus import RouteIdentifier
from ..models.route_shape import RouteShape


class GTFSRepositoryPort(ABC):
    """
    Port for accessing GTFS (General Transit Feed Specification) data.

    This port defines the interface for retrieving route shapes and
    geographic information from GTFS databases.
    """

    @abstractmethod
    def get_route_shape(self, route: RouteIdentifier) -> RouteShape | None:
        """
        Get the geographic shape of a route.

        Args:
            route: Route identifier with bus_line and direction

        Returns:
            RouteShape with ordered coordinates, or None if route not found
        """
        pass
