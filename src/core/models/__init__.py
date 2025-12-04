"""Domain models - Pure Python classes representing business entities."""

from .bus import BusPosition, BusRoute, RouteIdentifier
from .coordinate import Coordinate
from .trip import Trip
from .user import User
from .user_history import HistoryEntry, UserHistory

__all__ = [
    "User",
    "Trip",
    "UserHistory",
    "HistoryEntry",
    "Coordinate",
    "RouteIdentifier",
    "BusRoute",
    "BusPosition",
]
