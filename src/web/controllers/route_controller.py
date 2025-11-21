"""
Route controller - API endpoints for bus routes and positions.

This controller handles queries for real-time bus information.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...adapters.external.sptrans_adapter import SpTransAdapter
from ...config import settings
from ...core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ...core.services.route_service import RouteService
from ..mappers import (
    map_bus_position_list_to_schema,
    map_route_identifier_schema_to_domain,
)
from ..schemas import BusPositionsRequest, BusPositionsResponse

router = APIRouter(prefix="/routes", tags=["routes"])


def get_route_service() -> RouteService:
    """
    Dependency that provides a RouteService instance.

    Returns:
        Configured RouteService instance
    """
    bus_provider = SpTransAdapter(
        api_token=settings.sptrans_api_token,
        base_url=settings.sptrans_base_url,
    )
    return RouteService(bus_provider)


@router.post("/positions", response_model=BusPositionsResponse)
async def get_bus_positions(
    request: BusPositionsRequest,
    route_service: RouteService = Depends(get_route_service),
) -> BusPositionsResponse:
    """
    Retrieves the current positions of buses for the requested routes.

    Args:
        request (BusPositionsRequest): Request body containing a list of route identifiers.
        route_service (RouteService): Injected service that interacts with external providers.

    Returns:
        BusPositionsResponse: A response object containing the list of bus positions.

    Raises:
        HTTPException: If an unexpected error occurs while calling the external provider.
    """
    try:
        # Convert request schemas to domain RouteIdentifier objects
        route_identifiers: list[RouteIdentifier] = [
            map_route_identifier_schema_to_domain(route_schema) for route_schema in request.routes
        ]

        # Accumulate results from all routes
        all_positions: list[BusPosition] = []

        for route_identifier in route_identifiers:
            # Resolve provider-specific route details (BusRoute with internal ID)
            bus_route: BusRoute = await route_service.get_route_details(route_identifier)

            # Fetch positions for this specific bus route
            route_positions: list[BusPosition] = await route_service.get_bus_positions(bus_route)

            all_positions.extend(route_positions)

        # Convert domain objects back to API schemas
        position_schemas = map_bus_position_list_to_schema(all_positions)

        response: BusPositionsResponse = BusPositionsResponse(buses=position_schemas)
        return response

    except Exception as e:
        detail: str = f"Failed to retrieve bus positions: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e
