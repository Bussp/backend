"""Bus Provider port - Interface for external bus tracking service."""

from abc import ABC, abstractmethod

from ..models.bus import BusPosition, BusRoute


class BusProviderPort(ABC):
    """
    Abstract interface for bus tracking API integration.

    This port defines the contract for interacting with external
    bus tracking APIs (e.g., SPTrans, NextBus, etc.).
    Authentication is managed internally by implementations.
    """

    @abstractmethod
    async def get_bus_positions(
        self,
        route_id: int,
    ) -> list[BusPosition]:
        """
        Get real-time positions for specified routes.

        Args:
            route_ids: List of provider-specific route IDs.

        Returns:
            List of current bus positions with route_id.

        Raises:
            RuntimeError: If API call fails or authentication fails.
        """
        pass

    @abstractmethod
    async def search_routes(self, query: str) -> list[BusRoute]:
        """
        Search for bus routes matching a query string.

        Args:
            query: Search term (e.g., route number or destination name).

        Returns:
            List of matching bus routes.

        Raises:
            RuntimeError: If API call fails or authentication fails.
        """
        pass
