"""
Trip repository adapter - Implementation of TripRepository port.

This adapter implements the TripRepository interface using SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models.trip import Trip
from ...core.ports.trip_repository import TripRepository
from ..database.mappers import map_trip_db_to_domain, map_trip_domain_to_db


class TripRepositoryAdapter(TripRepository):
    """
    SQLAlchemy implementation of the TripRepository port.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository adapter.

        Args:
            session: Async database session
        """
        self.session = session

    async def save_trip(self, trip: Trip) -> Trip:
        """
        Save a new trip to the database.

        Args:
            trip: Trip domain model to save

        Returns:
            The saved trip

        Raises:
            Exception: If trip data is invalid
        """
        # Convert domain model to database model
        trip_db = map_trip_domain_to_db(trip)

        # Save to database
        self.session.add(trip_db)
        await self.session.flush()

        # Return domain model
        return map_trip_db_to_domain(trip_db)
