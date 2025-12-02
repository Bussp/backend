"""User history domain model."""

from dataclasses import dataclass
from datetime import datetime

from .bus import RouteIdentifier
from .trip import Trip


@dataclass
class HistoryEntry:
    """
    A single entry in user's trip history.

    Attributes:
        date: When the trip occurred
        score: Points earned from this trip
        route: Route identifier containing bus_line and bus_direction
    """

    date: datetime
    score: int
    route: RouteIdentifier


@dataclass
class UserHistory:
    """
    User's trip history.

    Attributes:
        email: User's email
        trips: List of all trips made by the user
    """

    email: str
    trips: list[Trip]
