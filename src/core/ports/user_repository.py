"""User repository port - Interface for user data persistence."""

from abc import ABC, abstractmethod

from ..models.user import User


class UserRepository(ABC):
    """
    Abstract interface for user data operations.

    This port defines the contract that any user repository adapter must implement.
    It isolates the core business logic from specific database implementations.
    """

    @abstractmethod
    async def save_user(self, user: User) -> User:
        """
        Save a new user to the repository.

        Args:
            user: User entity to save

        Returns:
            The saved user with any generated fields populated

        Raises:
            Exception: If a user with the same email already exists
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_users_ordered_by_score(self) -> list[User]:
        """
        Get all users sorted by score in descending order.

        Returns:
            List of users ordered by score (highest first)
        """
        pass

    @abstractmethod
    async def add_user_score(self, email: str, score_to_add: int) -> User:
        """
        Add points to a user's score.

        Args:
            email: User's email address
            score_to_add: Points to add to the user's current score

        Returns:
            Updated user with new score

        Raises:
            Exception: If user not found
        """
        pass
