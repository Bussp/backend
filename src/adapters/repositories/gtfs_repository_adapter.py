"""GTFS repository adapter - SQLite implementation."""

from ...adapters.database.gtfs_connection import get_gtfs_db
from ...core.models.bus import RouteIdentifier
from ...core.models.coordinate import Coordinate
from ...core.models.route_shape import RouteShape, RouteShapePoint
from ...core.ports.gtfs_repository import GTFSRepositoryPort


class GTFSRepositoryAdapter(GTFSRepositoryPort):
    """
    SQLite adapter for GTFS repository.

    Implements the GTFS repository port using a SQLite database.
    """

    def get_route_shape(self, route: RouteIdentifier) -> RouteShape | None:
        """
        Get the geographic shape of a route from GTFS database.

        Args:
            route: Route identifier with bus_line and direction

        Returns:
            RouteShape with ordered coordinates, or None if route not found
        """
        with get_gtfs_db() as conn:
            # First, get the shape_id for this route filtering by route_id and direction_id
            # In GTFS, direction_id is 0 or 1, while our RouteIdentifier uses 1 or 2
            direction_id = route.bus_direction - 1  # Convert: 1->0, 2->1

            cursor = conn.execute(
                """
                SELECT DISTINCT shape_id
                FROM trips
                WHERE route_id = ? AND direction_id = ?
                LIMIT 1
                """,
                (route.bus_line, direction_id),
            )

            row = cursor.fetchone()
            if not row:
                return None

            shape_id = row["shape_id"]

            # Now get all shape points for this shape_id
            cursor = conn.execute(
                """
                SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled
                FROM shapes
                WHERE shape_id = ?
                ORDER BY shape_pt_sequence ASC
                """,
                (shape_id,),
            )

            points = []
            for row in cursor.fetchall():
                point = RouteShapePoint(
                    coordinate=Coordinate(
                        latitude=row["shape_pt_lat"],
                        longitude=row["shape_pt_lon"],
                    ),
                    sequence=row["shape_pt_sequence"],
                    distance_traveled=row["shape_dist_traveled"],
                )
                points.append(point)

            if not points:
                return None

            return RouteShape(
                route=route,
                shape_id=shape_id,
                points=points,
            )
