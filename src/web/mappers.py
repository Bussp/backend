"""
Mappers between web schemas (Pydantic) and core domain models.

These functions translate between the API layer and the domain layer,
maintaining the separation of concerns.
"""

from ..core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ..core.models.coordinate import Coordinate
from ..core.models.route_shape import RouteShape
from ..core.models.user import User
from .schemas import (
    BusPositionSchema,
    BusRouteSchema,
    CoordinateSchema,
    RouteIdentifierSchema,
    RouteShapeResponse,
    UserResponse,
)

# ===== User Mappers =====


def map_user_domain_to_response(user: User) -> UserResponse:
    """
    Map a User domain model to a UserResponse schema.

    Args:
        user: User domain model

    Returns:
        UserResponse schema
    """
    return UserResponse(
        name=user.name,
        email=user.email,
        score=user.score,
    )


def map_user_domain_list_to_response(users: list[User]) -> list[UserResponse]:
    """
    Map a list of User domain models to UserResponse schemas.

    Args:
        users: List of User domain models

    Returns:
        List of UserResponse schemas
    """
    return [map_user_domain_to_response(user) for user in users]


# ===== Route Mappers =====


def map_route_identifier_schema_to_domain(
    schema: RouteIdentifierSchema,
) -> RouteIdentifier:
    """
    Map a RouteIdentifierSchema to a RouteIdentifier domain model.

    Args:
        schema: RouteIdentifierSchema from API

    Returns:
        RouteIdentifier domain model
    """
    return RouteIdentifier(
        bus_line=schema.bus_line,
        bus_direction=schema.bus_direction,
    )


def map_route_identifier_domain_to_schema(
    route: RouteIdentifier,
) -> RouteIdentifierSchema:
    """
    Map a RouteIdentifier domain model to a RouteIdentifierSchema.

    Args:
        route: RouteIdentifier domain model

    Returns:
        RouteIdentifierSchema for API
    """
    return RouteIdentifierSchema(
        bus_line=route.bus_line,
        bus_direction=route.bus_direction,
    )


def map_bus_route_schema_to_domain(schema: BusRouteSchema) -> BusRoute:
    """
    Map a BusRouteSchema to a BusRoute domain model.

    Args:
        schema: BusRouteSchema from API

    Returns:
        BusRoute domain model
    """
    return BusRoute(
        route_id=schema.route_id,
        route=map_route_identifier_schema_to_domain(schema.route),
    )


def map_bus_route_schema_list_to_domain(
    schemas: list[BusRouteSchema],
) -> list[BusRoute]:
    """
    Map a list of BusRouteSchema to BusRoute domain models.

    Args:
        schemas: List of BusRouteSchema from API

    Returns:
        List of BusRoute domain models
    """
    return [map_bus_route_schema_to_domain(schema) for schema in schemas]


def map_bus_route_domain_to_schema(bus_route: BusRoute) -> BusRouteSchema:
    """
    Map a BusRoute domain model to a BusRouteSchema.

    Args:
        bus_route: BusRoute domain model

    Returns:
        BusRouteSchema for API
    """
    return BusRouteSchema(
        route_id=bus_route.route_id,
        route=map_route_identifier_domain_to_schema(bus_route.route),
    )


def map_bus_route_domain_list_to_schema(
    bus_routes: list[BusRoute],
) -> list[BusRouteSchema]:
    """
    Map a list of BusRoute domain models to BusRouteSchema list.

    Args:
        bus_routes: List of BusRoute domain models

    Returns:
        List of BusRouteSchema for API
    """
    return [map_bus_route_domain_to_schema(bus_route) for bus_route in bus_routes]


def map_coordinate_domain_to_schema(coord: Coordinate) -> CoordinateSchema:
    """
    Map a Coordinate domain model to a CoordinateSchema.

    Args:
        coord: Coordinate domain model

    Returns:
        CoordinateSchema for API
    """
    return CoordinateSchema(
        latitude=coord.latitude,
        longitude=coord.longitude,
    )


def map_bus_position_domain_to_schema(position: BusPosition) -> BusPositionSchema:
    """
    Map a BusPosition domain model to a BusPositionSchema.

    Args:
        position: BusPosition domain model

    Returns:
        BusPositionSchema for API
    """
    return BusPositionSchema(
        route=map_route_identifier_domain_to_schema(position.route),
        position=map_coordinate_domain_to_schema(position.position),
        time_updated=position.time_updated,
    )


def map_bus_position_list_to_schema(
    positions: list[BusPosition],
) -> list[BusPositionSchema]:
    """
    Map a list of BusPosition domain models to BusPositionSchema list.

    Args:
        positions: List of BusPosition domain models

    Returns:
        List of BusPositionSchema for API
    """
    return [map_bus_position_domain_to_schema(pos) for pos in positions]


# ===== Route Shape Mappers =====


def map_route_shape_to_response(shape: RouteShape) -> RouteShapeResponse:
    """
    Map a RouteShape domain model to a RouteShapeResponse.

    Args:
        shape: RouteShape domain model

    Returns:
        RouteShapeResponse for API
    """
    return RouteShapeResponse(
        route_id=shape.route_id,
        shape_id=shape.shape_id,
        points=[
            map_coordinate_domain_to_schema(point.coordinate) for point in shape.points
        ],
    )
