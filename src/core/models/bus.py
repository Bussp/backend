"""Bus-related domain models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .coordinate import Coordinate


class RouteIdentifier(BaseModel):
    """
    Identifier for a bus route.

    Attributes:
        bus_line: Bus line number (e.g., "8000")
        bus_direction: Direction (1 or 2)
    """

    bus_line: str
    bus_direction: Literal[1, 2] = Field(
        ..., description="Direction (1 = ida, 2 = volta)"
    )

    model_config = {"frozen": True}


class BusRoute(BaseModel):
    """
    Bus route information.

    Attributes:
        route_id: Unique identifier for this route
        route: Route identifier containing line and direction
    """

    route_id: int
    route: RouteIdentifier

    model_config = {"frozen": True}


class BusPosition(BaseModel):
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

    model_config = {"frozen": True}
