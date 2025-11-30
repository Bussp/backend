"""Trip service - Business logic for trip management."""

from datetime import datetime

from ..models.trip import Trip
from ..ports.trip_repository import TripRepository
from ..ports.user_repository import UserRepository


class TripService:
    """
    Service containing business logic for trip operations.

    This service orchestrates trip-related operations and score calculations.
    """

    def __init__(
        self,
        trip_repository: TripRepository,
        user_repository: UserRepository,
    ):
        """
        Initialize the trip service.

        Args:
            trip_repository: Implementation of TripRepository port
            user_repository: Implementation of UserRepository port
        """
        self.trip_repository = trip_repository
        self.user_repository = user_repository

    async def create_trip(
        self,
        email: str,
        bus_line: str,
        bus_direction: int,
        distance: int,
        trip_date: datetime,
    ) -> Trip:
        """
        Create a new trip and update user score.

        Business rule: Score is calculated based on distance traveled.
        For example: 1 point per 100 meters traveled.

        Args:
            email: User's email
            bus_line: Bus line taken
            bus_direction: Direction of travel
            distance: Distance traveled in meters
            trip_date: When the trip occurred

        Returns:
            The created trip with calculated score

        Raises:
            Exception: If user doesn't exist
        """
        # Verify user exists
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")

        # Calculate score (1 point per 100 meters)
        # Validate distance: negative distances are not allowed
        if distance < 0:
            raise ValueError("distance must be non-negative")

        score = (distance // 1000) * 77

        # Create trip
        trip = Trip(
            email=email,
            bus_line=bus_line,
            bus_direction=bus_direction,
            distance=distance,
            score=score,
            start_date=trip_date,
            end_date=trip_date,  # In a real app, this would be calculated
        )

        # Save trip
        saved_trip = await self.trip_repository.save_trip(trip)

        # Update user score
        await self.user_repository.add_user_score(email, score)

        return saved_trip
