"""
Mappers for converting SPTrans API schemas to domain models.

These mappers handle the transformation between external API DTOs
and internal domain objects, keeping the adapter layer clean.
"""

from ...core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ...core.models.coordinate import Coordinate
from .sptrans_schemas import SPTransLineInfo, SPTransLineSearchResponse, SPTransPositionsResponse, SPTransVehicle

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
    for item in data.results:
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
    return BusRoute(
        route_id=line_info.cl,
        route=map_line_info_to_route_identifier(line_info),
    )

def map_line_info_to_route_identifier(line_info: SPTransLineInfo) -> RouteIdentifier:
    """
    Convert SPTrans line info to domain RouteIdentifier.

    Args:
        line_info: SPTrans line information.

    Returns:
        Domain RouteIdentifier with formatted bus_line (lt-tl format).
    """
    bus_line = f"{line_info.lt}-{line_info.tl}"
    return RouteIdentifier(
        bus_line=bus_line,
        bus_direction=line_info.sl,
    )


def map_positions_response_to_bus_positions(
    data: SPTransPositionsResponse,
    route: RouteIdentifier,
) -> list[BusPosition]:
    """
    Convert API positions response to list of BusPosition domain objects.

    Args:
        data: SPTransPositionsResponse object.
        route: RouteIdentifier for all vehicles in this response.

    Returns:
        List of domain BusPosition objects.
    """
    positions: list[BusPosition] = []

    for vehicle in data.vs:
        position = map_vehicle_to_bus_position(vehicle, route)
        positions.append(position)

    return positions

def map_vehicle_to_bus_position(
    vehicle: SPTransVehicle,
    route: RouteIdentifier,
) -> BusPosition:
    """
    Convert SPTrans vehicle to domain BusPosition.

    Args:
        vehicle: SPTransVehicle position data.
        route: RouteIdentifier for this vehicle's route.

    Returns:
        Domain BusPosition with coordinates and route info.
    """
    return BusPosition(
        route=route,
        position=Coordinate(
            latitude=vehicle.py,
            longitude=vehicle.px,
        ),
        time_updated=vehicle.ta,
    )
