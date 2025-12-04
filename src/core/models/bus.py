"""Bus-related domain models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .coordinate import Coordinate

BusDirection = Literal[1, 2]


class RouteIdentifier(BaseModel):
    """
    Identifier for a bus route.

    Attributes:
        bus_line: Bus line number (e.g., "8000")
        bus_direction: Direction (1 or 2)
    """

    bus_line: str
    bus_direction: BusDirection = Field(..., description="Direction (1 = ida, 2 = volta)")

    model_config = {"frozen": True}


class BusRoute(BaseModel):
    """
    Bus route information.

    Attributes:
        route_id: Unique identifier for this route
        route: Route identifier containing line and direction
        is_circular: Whether the route is circular
        terminal_name: Terminal name (primary if direction=1, secondary if direction=2)
    """

    route_id: int
    route: RouteIdentifier
    is_circular: bool = Field(..., description="Whether the route is circular")
    terminal_name: str = Field(
        ...,
        description="Terminal name (primary if direction=1, secondary if direction=2)",
    )

    model_config = {"frozen": True}


class BusPosition(BaseModel):
    """
    Real-time position of a bus.

    Attributes:
        route_id: Provider-specific route identifier
        position: Geographic coordinate of the bus
        time_updated: Last update timestamp
    """

    route_id: int
    position: Coordinate
    time_updated: datetime

    model_config = {"frozen": True}
