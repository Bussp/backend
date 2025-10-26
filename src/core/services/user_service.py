"""User service - Business logic for user management."""

from ..models.user import User
from ..ports.password_hasher import PasswordHasherPort
from ..ports.user_repository import UserRepository


class UserService:
    """
    Service containing business logic for user operations.

    This service orchestrates user-related operations using the repository port.
    It depends on abstractions (ports), not concrete implementations.
    """

    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasherPort):
        """
        Initialize the user service.

        Args:
            user_repository: Implementation of UserRepository port
        """
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def create_user(self, name: str, email: str, password: str) -> User:
        """
        Create a new user in the system.

        Args:
            name: User's full name
            email: User's email address
            password: User's password in plain text (will be hashed internally)

        Returns:
            The created user

        Raises:
            Exception: If user with email already exists
        """
        # Check if user already exists
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        hashed = self.password_hasher.hash(password)
        user = User(name=name, email=email, password=hashed, score=0)
        return await self.user_repository.save_user(user)

    async def get_user(self, email: str) -> User | None:
        """
        Retrieve a user by email.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        return await self.user_repository.get_user_by_email(email)

    async def login_user(self, email: str, password: str) -> User | None:
        """
        Authenticate a user.

        Args:
            email: User's email
            password: User's password in plain text

        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            return None
        if self.password_hasher.verify(password, user.password):
            return user
        return None
