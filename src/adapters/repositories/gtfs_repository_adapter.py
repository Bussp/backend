"""GTFS repository adapter - SQLite implementation."""

from ...adapters.database.gtfs_connection import get_gtfs_db
from ...core.models.coordinate import Coordinate
from ...core.models.route_shape import RouteShape, RouteShapePoint
from ...core.ports.gtfs_repository import GTFSRepositoryPort


class GTFSRepositoryAdapter(GTFSRepositoryPort):
    """
    SQLite adapter for GTFS repository.

    Implements the GTFS repository port using a SQLite database.
    """

    def get_route_shape(self, route_id: str) -> RouteShape | None:
        """
        Get the geographic shape of a route from GTFS database.

        Args:
            route_id: Route identifier

        Returns:
            RouteShape with ordered coordinates, or None if route not found
        """
        with get_gtfs_db() as conn:
            # First, get the shape_id for this route
            cursor = conn.execute(
                """
                SELECT DISTINCT shape_id
                FROM trips
                WHERE route_id = ?
                LIMIT 1
                """,
                (route_id,),
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
                route_id=route_id,
                shape_id=shape_id,
                points=points,
            )
