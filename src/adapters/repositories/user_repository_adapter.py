"""
User repository adapter - Implementation of UserRepository port.

This adapter implements the UserRepository interface using SQLAlchemy.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models.user import User
from ...core.ports.user_repository import UserRepository
from ..database.mappers import (
    map_user_db_list_to_domain,
    map_user_db_to_domain,
    map_user_domain_to_db,
)
from ..database.models import UserDB


class UserRepositoryAdapter(UserRepository):
    """
    SQLAlchemy implementation of the UserRepository port.

    This adapter translates between domain models and database models.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository adapter.

        Args:
            session: Async database session
        """
        self.session = session

    async def save_user(self, user: User) -> User:
        """
        Save a new user to the database.

        Args:
            user: User domain model to save

        Returns:
            The saved user

        Raises:
            Exception: If user with email already exists
        """
        # Check if user exists
        existing = await self.get_user_by_email(user.email)
        if existing:
            raise ValueError(f"User with email {user.email} already exists")

        # Convert domain model to database model
        user_db = map_user_domain_to_db(user)

        # Save to database
        self.session.add(user_db)
        await self.session.flush()

        # Return domain model
        return map_user_db_to_domain(user_db)

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(select(UserDB).where(UserDB.email == email))
        user_db = result.scalar_one_or_none()

        if user_db is None:
            return None

        return map_user_db_to_domain(user_db)

    async def get_all_users_ordered_by_score(self) -> list[User]:
        """
        Get all users sorted by score in descending order.

        Returns:
            List of users ordered by score (highest first)
        """
        result = await self.session.execute(select(UserDB).order_by(UserDB.score.desc()))
        users_db = result.scalars().all()

        return map_user_db_list_to_domain(list(users_db))

    async def add_user_score(self, email: str, score_to_add: int) -> User:
        """
        Add points to a user's score.

        Args:
            email: User's email address
            score_to_add: Points to add

        Returns:
            Updated user

        Raises:
            Exception: If user not found
        """
        # Update score
        await self.session.execute(
            update(UserDB).where(UserDB.email == email).values(score=UserDB.score + score_to_add)
        )

        # Fetch updated user
        user = await self.get_user_by_email(email)
        if user is None:
            raise ValueError(f"User with email {email} not found")

        return user
