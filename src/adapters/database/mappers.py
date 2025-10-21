"""
Mappers between database models (SQLAlchemy) and domain models.

These functions translate between the persistence layer and the domain layer.
"""

from ...core.models.trip import Trip
from ...core.models.user import User
from ...core.models.user_history import UserHistory
from .models import TripDB, UserDB

# ===== User Mappers =====


def map_user_db_to_domain(user_db: UserDB) -> User:
    """
    Map a UserDB (SQLAlchemy model) to a User (domain model).

    Args:
        user_db: SQLAlchemy user model

    Returns:
        User domain model
    """
    return User(
        name=user_db.name,
        email=user_db.email,
        score=user_db.score,
        password=user_db.password,
    )


def map_user_domain_to_db(user: User) -> UserDB:
    """
    Map a User (domain model) to a UserDB (SQLAlchemy model).

    Args:
        user: User domain model

    Returns:
        SQLAlchemy user model
    """
    return UserDB(
        name=user.name,
        email=user.email,
        score=user.score,
        password=user.password,
    )


def map_user_db_list_to_domain(users_db: list[UserDB]) -> list[User]:
    """
    Map a list of UserDB models to User domain models.

    Args:
        users_db: List of SQLAlchemy user models

    Returns:
        List of User domain models
    """
    return [map_user_db_to_domain(user_db) for user_db in users_db]


# ===== Trip Mappers =====


def map_trip_db_to_domain(trip_db: TripDB) -> Trip:
    """
    Map a TripDB (SQLAlchemy model) to a Trip (domain model).

    Args:
        trip_db: SQLAlchemy trip model

    Returns:
        Trip domain model
    """
    return Trip(
        email=trip_db.email,
        bus_line=trip_db.bus_line,
        bus_direction=trip_db.bus_direction,
        distance=trip_db.distance,
        score=trip_db.score,
        start_date=trip_db.start_date,
        end_date=trip_db.end_date,
    )


def map_trip_domain_to_db(trip: Trip) -> TripDB:
    """
    Map a Trip (domain model) to a TripDB (SQLAlchemy model).

    Args:
        trip: Trip domain model

    Returns:
        SQLAlchemy trip model
    """
    return TripDB(
        email=trip.email,
        bus_line=trip.bus_line,
        bus_direction=trip.bus_direction,
        distance=trip.distance,
        score=trip.score,
        start_date=trip.start_date,
        end_date=trip.end_date,
    )


def map_trip_db_list_to_domain(trips_db: list[TripDB]) -> list[Trip]:
    """
    Map a list of TripDB models to Trip domain models.

    Args:
        trips_db: List of SQLAlchemy trip models

    Returns:
        List of Trip domain models
    """
    return [map_trip_db_to_domain(trip_db) for trip_db in trips_db]


# ===== History Mappers =====


def map_user_with_trips_to_history(user_db: UserDB) -> UserHistory:
    """
    Map a UserDB with trips to a UserHistory domain model.

    Args:
        user_db: SQLAlchemy user model with trips loaded

    Returns:
        UserHistory domain model
    """
    trips = map_trip_db_list_to_domain(user_db.trips)
    return UserHistory(email=user_db.email, trips=trips)
