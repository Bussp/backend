"""History service - Business logic for user trip history."""

from typing import List, Optional
from datetime import datetime

from ..models.user_history import UserHistory
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

    async def get_user_history(self, email: str) -> Optional[UserHistory]:
        """
        Get a user's complete trip history.

        Args:
            email: User's email

        Returns:
            User's history with all trips, or None if no history found
        """
        return await self.history_repository.get_user_history(email)

    async def get_user_history_summary(self, email: str) -> tuple[List[datetime], List[int]]:
        """
        Get a summary of user's history as dates and scores.

        Args:
            email: User's email

        Returns:
            Tuple of (dates, scores) lists
        """
        history = await self.history_repository.get_user_history(email)

        if not history or not history.trips:
            return ([], [])

        dates = [trip.start_date for trip in history.trips]
        scores = [trip.score for trip in history.trips]

        return (dates, scores)
