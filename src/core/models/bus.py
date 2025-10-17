"""Bus-related domain models."""

from dataclasses import dataclass
from datetime import datetime

from .coordinate import Coordinate


@dataclass
class RouteIdentifier:
    """
    Identifier for a bus route.

    Attributes:
        bus_line: Bus line number (e.g., "8000")
        bus_direction: Direction (1 or 2)
    """

    bus_line: str
    bus_direction: int


@dataclass
class BusRoute:
    """
    Bus route information.

    Attributes:
        route_id: Unique identifier for this route
        route: Route identifier containing line and direction
    """

    route_id: int
    route: RouteIdentifier


@dataclass
class BusPosition:
    """
    Real-time position of a bus.

    Attributes:
        route: Route identifier for this bus
        position: Geographic coordinate of the bus
        time_updated: Last update timestamp
    """

    route: RouteIdentifier
    position: Coordinate
    time_updated: datetime
