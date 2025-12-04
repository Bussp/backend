"""Route shape domain model."""

from dataclasses import dataclass

from .bus import RouteIdentifier
from .coordinate import Coordinate


@dataclass
class RouteShapePoint:
    """
    A single point in a route shape.

    Attributes:
        coordinate: Geographic coordinate
        sequence: Point sequence in the route
        distance_traveled: Optional distance traveled along the route
    """

    coordinate: Coordinate
    sequence: int
    distance_traveled: float | None = None


@dataclass
class RouteShape:
    """
    Complete shape of a route with ordered coordinates.

    Attributes:
        route: Route identifier (bus_line and direction)
        shape_id: Shape identifier from GTFS
        points: List of points defining the route shape, ordered by sequence
    """

    route: RouteIdentifier
    shape_id: str
    points: list[RouteShapePoint]
