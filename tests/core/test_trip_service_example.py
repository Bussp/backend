"""
Example test demonstrating how to test the core layer in isolation.

This test shows how Hexagonal Architecture enables testing business logic
without any infrastructure dependencies (no database, no HTTP, no external APIs).
"""

import pytest
from datetime import datetime
from typing import List, Optional

from src.core.models.user import User
from src.core.models.trip import Trip
from src.core.ports.user_repository import UserRepository
from src.core.ports.trip_repository import TripRepository
from src.core.services.trip_service import TripService


# ===== Mock Implementations (Test Doubles) =====


class MockUserRepository(UserRepository):
    """Mock user repository for testing."""

    def __init__(self):
        self.users: dict[str, User] = {}

    async def save_user(self, user: User) -> User:
        if user.email in self.users:
            raise ValueError(f"User with email {user.email} already exists")
        self.users[user.email] = user
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return self.users.get(email)

    async def get_all_users_ordered_by_score(self) -> List[User]:
        return sorted(self.users.values(), key=lambda u: u.score, reverse=True)

    async def add_user_score(self, email: str, score_to_add: int) -> User:
        user = self.users.get(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        user.score += score_to_add
        return user


class MockTripRepository(TripRepository):
    """Mock trip repository for testing."""

    def __init__(self):
        self.trips: List[Trip] = []

    async def save_trip(self, trip: Trip) -> Trip:
        self.trips.append(trip)
        return trip


# ===== Tests =====


@pytest.mark.asyncio
async def test_create_trip_calculates_score_correctly():
    """
    Test that trip creation calculates score based on distance.

    This test demonstrates testing business logic without any database.
    """
    # Arrange: Set up mock repositories
    user_repo = MockUserRepository()
    trip_repo = MockTripRepository()

    # Create a test user
    test_user = User(name="Test User", email="test@example.com", score=0, password="hashed")
    await user_repo.save_user(test_user)

    # Create the service with mock repositories
    trip_service = TripService(trip_repo, user_repo)

    # Act: Create a trip with 1000 meters distance
    trip = await trip_service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        trip_date=datetime.now(),
    )

    # Assert: Score should be distance / 100 = 10 points
    assert trip.score == 10
    assert len(trip_repo.trips) == 1


@pytest.mark.asyncio
async def test_create_trip_updates_user_score():
    """Test that creating a trip updates the user's total score."""
    # Arrange
    user_repo = MockUserRepository()
    trip_repo = MockTripRepository()

    test_user = User(name="Test User", email="test@example.com", score=0, password="hashed")
    await user_repo.save_user(test_user)

    trip_service = TripService(trip_repo, user_repo)

    # Act: Create two trips
    await trip_service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=500,  # 5 points
        trip_date=datetime.now(),
    )

    await trip_service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=2,
        distance=1500,  # 15 points
        trip_date=datetime.now(),
    )

    # Assert: User should have 20 total points
    updated_user = await user_repo.get_user_by_email("test@example.com")
    assert updated_user is not None
    assert updated_user.score == 20


@pytest.mark.asyncio
async def test_create_trip_fails_for_nonexistent_user():
    """Test that creating a trip for a non-existent user raises an error."""
    # Arrange
    user_repo = MockUserRepository()
    trip_repo = MockTripRepository()
    trip_service = TripService(trip_repo, user_repo)

    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await trip_service.create_trip(
            email="nonexistent@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )


"""
Key Takeaways:

1. **No Database Required**: Tests run instantly without any database setup
2. **No HTTP Required**: We test services directly without FastAPI
3. **Full Control**: Mock repositories let us control exactly what data exists
4. **Business Logic Focus**: We're testing the scoring algorithm, not infrastructure
5. **Fast & Reliable**: No flaky tests due to database or network issues

This is the power of Hexagonal Architecture - pure, fast, isolated unit tests!
"""
