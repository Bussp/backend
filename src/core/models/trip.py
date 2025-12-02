"""Trip domain model."""

from dataclasses import dataclass
from datetime import datetime

from .bus import RouteIdentifier


@dataclass
class Trip:
    """
    Trip entity representing a user's bus journey.

    Attributes:
        email: Email of the user who made the trip
        route: Route identifier containing bus_line and bus_direction
        distance: Distance traveled in meters
        score: Points earned from this trip
        trip_date: When the trip occurred
    """

    email: str
    route: RouteIdentifier
    distance: int
    score: int
    trip_date: datetime
