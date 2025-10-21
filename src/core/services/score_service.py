"""Score service - Business logic for ranking and scoring."""


from ..models.user import User
from ..ports.user_repository import UserRepository


class ScoreService:
    """
    Service containing business logic for scoring and ranking operations.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize the score service.

        Args:
            user_repository: Implementation of UserRepository port
        """
        self.user_repository = user_repository

    async def get_user_ranking(self, email: str) -> int | None:
        """
        Get a user's position in the global ranking.

        Args:
            email: User's email

        Returns:
            User's rank (1-based), or None if user not found
        """
        all_users = await self.user_repository.get_all_users_ordered_by_score()

        for index, user in enumerate(all_users, start=1):
            if user.email == email:
                return index

        return None

    async def get_global_ranking(self) -> list[User]:
        """
        Get the global user ranking.

        Returns:
            List of all users ordered by score (highest first)
        """
        return await self.user_repository.get_all_users_ordered_by_score()
