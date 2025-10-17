"""User service - Business logic for user management."""

from typing import Optional

from ..models.user import User
from ..ports.user_repository import UserRepository


class UserService:
    """
    Service containing business logic for user operations.

    This service orchestrates user-related operations using the repository port.
    It depends on abstractions (ports), not concrete implementations.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize the user service.

        Args:
            user_repository: Implementation of UserRepository port
        """
        self.user_repository = user_repository

    async def create_user(self, name: str, email: str, password: str) -> User:
        """
        Create a new user in the system.

        Args:
            name: User's full name
            email: User's email address
            password: User's password (should be hashed before calling this)

        Returns:
            The created user

        Raises:
            Exception: If user with email already exists
        """
        # Check if user already exists
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Create new user
        user = User(name=name, email=email, password=password, score=0)
        return await self.user_repository.save_user(user)

    async def get_user(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        return await self.user_repository.get_user_by_email(email)

    async def login_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            email: User's email
            password: User's password (hashed)

        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.user_repository.get_user_by_email(email)
        if user and user.password == password:
            return user
        return None
