"""User history repository port - Interface for retrieving user trip history."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.user_history import UserHistory


class UserHistoryRepository(ABC):
    """
    Abstract interface for user history operations.

    This port defines the contract for retrieving user trip history.
    """

    @abstractmethod
    async def get_user_history(self, email: str) -> Optional[UserHistory]:
        """
        Retrieve a user's complete trip history.

        Args:
            email: User's email address

        Returns:
            UserHistory containing all trips, or None if user has no history
        """
        pass
