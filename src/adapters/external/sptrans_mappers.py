"""
Mappers for converting SPTrans API schemas to domain models.

These mappers handle the transformation between external API DTOs
and internal domain objects, keeping the adapter layer clean.
"""

from typing import cast

from ...core.models.bus import BusDirection, BusPosition, BusRoute, RouteIdentifier
from ...core.models.coordinate import Coordinate
from .sptrans_schemas import (
    SPTransLineInfo,
    SPTransLineSearchResponse,
    SPTransPositionsResponse,
    SPTransVehicle,
)


def map_search_response_to_bus_route_list(
    data: SPTransLineSearchResponse,
) -> list[BusRoute]:
    """
    Convert API search response to list of BusRoute domain objects.

    Args:
        data: SPTransLineSearchResponse object.

    Returns:
        List of BusRoute domain objects.
    """
    bus_route_list: list[BusRoute] = []
    for item in data.root:
        bus_route_list.append(map_line_info_to_bus_route(item))
    return bus_route_list


def map_line_info_to_bus_route(line_info: SPTransLineInfo) -> BusRoute:
    """
    Convert SPTrans line info to domain BusRoute.

    Args:
        line_info: SPTrans line information.

    Returns:
        Domain BusRoute with route_id and identifier.
    """
    # Terminal name: primary if direction=1 (ida), secondary if direction=2 (volta)
    terminal_name = (
        line_info.primary_terminal if line_info.direction == 1 else line_info.secondary_terminal
    )
    return BusRoute(
        route_id=line_info.route_id,
        route=map_line_info_to_route_identifier(line_info),
        is_circular=line_info.is_circular,
        terminal_name=terminal_name,
    )


def map_line_info_to_route_identifier(line_info: SPTransLineInfo) -> RouteIdentifier:
    """
    Convert SPTrans line info to domain RouteIdentifier.

    Args:
        line_info: SPTrans line information.

    Returns:
        Domain RouteIdentifier with formatted bus_line (line_number-line_sufix format).
    """
    bus_line = f"{line_info.line_number}-{line_info.line_sufix}"
    return RouteIdentifier(
        bus_line=bus_line,
        bus_direction=cast(BusDirection, line_info.direction),
    )


def map_positions_response_to_bus_positions(
    data: SPTransPositionsResponse,
    route_id: int,
) -> list[BusPosition]:
    """
    Convert API positions response to list of BusPosition domain objects.

    Args:
        data: SPTransPositionsResponse object.
        route_id: Provider-specific route identifier.

    Returns:
        List of domain BusPosition objects.
    """
    positions: list[BusPosition] = []

    for vehicle in data.vehicles:
        position = map_vehicle_to_bus_position(vehicle, route_id)
        positions.append(position)

    return positions


def map_vehicle_to_bus_position(
    vehicle: SPTransVehicle,
    route_id: int,
) -> BusPosition:
    """
    Convert SPTrans vehicle to domain BusPosition.

    Args:
        vehicle: SPTransVehicle position data.
        route_id: Provider-specific route identifier.

    Returns:
        Domain BusPosition with coordinates and route_id.
    """
    return BusPosition(
        route_id=route_id,
        position=Coordinate(
            latitude=vehicle.latitude,
            longitude=vehicle.longitude,
        ),
        time_updated=vehicle.time_updated,
    )
