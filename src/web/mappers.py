"""
Mappers between web schemas (Pydantic) and core domain models.

These functions translate between the API layer and the domain layer,
maintaining the separation of concerns.
"""

from typing import cast

from ..core.models.bus import BusDirection, BusPosition, BusRoute, RouteIdentifier
from ..core.models.coordinate import Coordinate
from ..core.models.route_shape import RouteShape
from ..core.models.user import User
from ..core.models.user_history import HistoryEntry
from .schemas import (
    BusPositionSchema,
    BusRouteRequestSchema,
    BusRouteResponseSchema,
    CoordinateSchema,
    HistoryResponse,
    RankingUserResponse,
    RouteIdentifierSchema,
    RouteShapeResponse,
    TripHistoryEntry,
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


def map_user_domain_to_ranking_response(user: User) -> RankingUserResponse:
    """
    Map a User domain model to a RankingUserResponse schema (excludes email).

    Args:
        user: User domain model

    Returns:
        RankingUserResponse schema
    """
    return RankingUserResponse(
        name=user.name,
        score=user.score,
    )


def map_user_domain_list_to_ranking_response(
    users: list[User],
) -> list[RankingUserResponse]:
    """
    Map a list of User domain models to RankingUserResponse schemas (excludes email).

    Args:
        users: List of User domain models

    Returns:
        List of RankingUserResponse schemas
    """
    return [map_user_domain_to_ranking_response(user) for user in users]


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
        bus_direction=cast(BusDirection, schema.bus_direction),
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


def map_bus_route_request_to_route_id(
    schema: BusRouteRequestSchema,
) -> int:
    """
    Extract route_id from a BusRouteRequestSchema.

    Args:
        schema: BusRouteRequestSchema from API request

    Returns:
        route_id (int)
    """
    return schema.route_id


def map_bus_route_request_list(
    schemas: list[BusRouteRequestSchema],
) -> list[int]:
    """
    Map a list of BusRouteRequestSchema to a list of route_ids.

    Args:
        schemas: List of BusRouteRequestSchema from API request

    Returns:
        List of route_ids
    """
    return [schema.route_id for schema in schemas]


def map_bus_route_domain_to_schema(bus_route: BusRoute) -> BusRouteResponseSchema:
    """
    Map a BusRoute domain model to a BusRouteResponseSchema.

    Args:
        bus_route: BusRoute domain model

    Returns:
        BusRouteResponseSchema for API response
    """
    return BusRouteResponseSchema(
        route_id=bus_route.route_id,
        route=map_route_identifier_domain_to_schema(bus_route.route),
        is_circular=bus_route.is_circular,
        terminal_name=bus_route.terminal_name,
    )


def map_bus_route_domain_list_to_schema(
    bus_routes: list[BusRoute],
) -> list[BusRouteResponseSchema]:
    """
    Map a list of BusRoute domain models to BusRouteResponseSchema list.

    Args:
        bus_routes: List of BusRoute domain models

    Returns:
        List of BusRouteResponseSchema for API response
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
        route_id=position.route_id,
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
        route=map_route_identifier_domain_to_schema(shape.route),
        shape_id=shape.shape_id,
        points=[map_coordinate_domain_to_schema(point.coordinate) for point in shape.points],
    )


def map_route_shapes_to_response(shapes: list[RouteShape]) -> list[RouteShapeResponse]:
    """
    Map a list of RouteShape domain models to RouteShapeResponse list.

    Args:
        shapes: List of RouteShape domain models

    Returns:
        List of RouteShapeResponse for API
    """
    return [map_route_shape_to_response(shape) for shape in shapes]


# ===== History Mappers =====


def map_history_entry_to_schema(entry: HistoryEntry) -> TripHistoryEntry:
    """
    Map a HistoryEntry domain model to a TripHistoryEntry schema.

    Args:
        entry: HistoryEntry domain model

    Returns:
        TripHistoryEntry schema for API
    """
    return TripHistoryEntry(
        date=entry.date,
        score=entry.score,
        route=map_route_identifier_domain_to_schema(entry.route),
    )


def map_history_entries_to_response(entries: list[HistoryEntry]) -> HistoryResponse:
    """
    Map a list of HistoryEntry domain models to a HistoryResponse.

    Args:
        entries: List of HistoryEntry domain models

    Returns:
        HistoryResponse for API
    """
    return HistoryResponse(trips=[map_history_entry_to_schema(entry) for entry in entries])
