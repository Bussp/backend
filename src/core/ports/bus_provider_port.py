"""Bus Provider port - Interface for external bus tracking service."""

from abc import ABC, abstractmethod
from typing import List

from ..models.bus import BusPosition, BusRoute, RouteIdentifier


class BusProviderPort(ABC):
    """
    Abstract interface for bus tracking API integration.

    This port defines the contract for interacting with external
    bus tracking APIs (e.g., SPTrans, NextBus, etc.).
    """

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the bus tracking API.

        Returns:
            True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_bus_positions(
        self, routes: List[RouteIdentifier]
    ) -> List[BusPosition]:
        """
        Get real-time positions for specified bus routes.

        Args:
            routes: List of route identifiers to query

        Returns:
            List of current bus positions

        Raises:
            Exception: If API call fails or authentication required
        """
        pass

    @abstractmethod
    async def get_route_details(self, route: RouteIdentifier) -> BusRoute:
        """
        Get detailed information about a specific route.

        Args:
            route: Route identifier to query

        Returns:
            Bus route details

        Raises:
            Exception: If route not found or API call fails
        """
        pass
