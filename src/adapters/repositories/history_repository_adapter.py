"""
History repository adapter - Implementation of UserHistoryRepository port.

This adapter implements the UserHistoryRepository interface using SQLAlchemy.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.models.user_history import UserHistory
from ...core.ports.history_repository import UserHistoryRepository
from ..database.mappers import map_user_with_trips_to_history
from ..database.models import UserDB


class UserHistoryRepositoryAdapter(UserHistoryRepository):
    """
    SQLAlchemy implementation of the UserHistoryRepository port.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository adapter.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_user_history(self, email: str) -> Optional[UserHistory]:
        """
        Retrieve a user's complete trip history.

        Args:
            email: User's email address

        Returns:
            UserHistory with all trips, or None if user has no history
        """
        # Query user with trips eagerly loaded
        result = await self.session.execute(
            select(UserDB).where(UserDB.email == email).options(selectinload(UserDB.trips))
        )
        user_db = result.scalar_one_or_none()

        if user_db is None or not user_db.trips:
            return None

        return map_user_with_trips_to_history(user_db)
