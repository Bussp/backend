"""History service - Business logic for user trip history."""

from ..models.user_history import HistoryEntry
from ..ports.history_repository import UserHistoryRepository


class HistoryService:
    """
    Service containing business logic for user history operations.
    """

    def __init__(self, history_repository: UserHistoryRepository):
        """
        Initialize the history service.

        Args:
            history_repository: Implementation of UserHistoryRepository port
        """
        self.history_repository = history_repository

    async def get_user_history(self, email: str) -> list[HistoryEntry]:
        """
        Get a summary of user's history as a list of HistoryEntry objects.

        Args:
            email: User's email

        Returns:
            List of HistoryEntry objects containing date, score, and route_identifier
        """
        history = await self.history_repository.get_user_history(email)

        if not history or not history.trips:
            return []

        return [
            HistoryEntry(
                date=trip.trip_date,
                score=trip.score,
                route=trip.route,
            )
            for trip in history.trips
        ]
