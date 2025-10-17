"""Trip repository port - Interface for trip data persistence."""

from abc import ABC, abstractmethod

from ..models.trip import Trip


class TripRepository(ABC):
    """
    Abstract interface for trip data operations.

    This port defines the contract that any trip repository adapter must implement.
    """

    @abstractmethod
    async def save_trip(self, trip: Trip) -> Trip:
        """
        Save a new trip to the repository.

        Args:
            trip: Trip entity to save

        Returns:
            The saved trip

        Raises:
            Exception: If trip data is invalid or user doesn't exist
        """
        pass
