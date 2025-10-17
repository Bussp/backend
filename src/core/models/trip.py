"""Trip domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trip:
    """
    Trip entity representing a user's bus journey.

    Attributes:
        email: Email of the user who made the trip
        bus_line: Bus line identifier (e.g., "8000")
        bus_direction: Direction of the bus (1 or 2)
        distance: Distance traveled in meters
        score: Points earned from this trip
        start_date: When the trip started
        end_date: When the trip ended
    """

    email: str
    bus_line: str
    bus_direction: int
    distance: int
    score: int
    start_date: datetime
    end_date: datetime
