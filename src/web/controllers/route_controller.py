"""
Route controller - API endpoints for bus routes and positions.

This controller handles queries for real-time bus information and route shapes.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...adapters.external.sptrans_adapter import SpTransAdapter
from ...adapters.repositories.gtfs_repository_adapter import GTFSRepositoryAdapter
from ...config import settings
from ...core.services.route_service import RouteService
from ..mappers import (
    map_bus_position_list_to_schema,
    map_route_identifier_schema_to_domain,
    map_route_shape_to_response,
)
from ..schemas import BusPositionsRequest, BusPositionsResponse, RouteShapeResponse

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
    gtfs_repository = GTFSRepositoryAdapter()
    return RouteService(bus_provider, gtfs_repository)


@router.post("/positions", response_model=BusPositionsResponse)
async def get_bus_positions(
    request: BusPositionsRequest,
    route_service: RouteService = Depends(get_route_service),
) -> BusPositionsResponse:
    """
    Get current positions for specified bus routes.

    Args:
        request: Request with list of routes to query
        route_service: Injected route service

    Returns:
        Current positions of buses on the requested routes

    Raises:
        HTTPException: If external API fails
    """
    try:
        # Map schemas to domain models
        route_identifiers = [
            map_route_identifier_schema_to_domain(route) for route in request.routes
        ]

        # Get positions from service
        positions = await route_service.get_bus_positions(route_identifiers)

        # Map back to schemas
        position_schemas = map_bus_position_list_to_schema(positions)

        return BusPositionsResponse(buses=position_schemas)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bus positions: {str(e)}",
        ) from e


@router.get("/shape/{route_id}", response_model=RouteShapeResponse)
async def get_route_shape(
    route_id: str,
    route_service: RouteService = Depends(get_route_service),
) -> RouteShapeResponse:
    """
    Get the geographic shape (coordinates) of a route from GTFS data.

    Args:
        route_id: Route identifier (e.g., "1012-10")
        route_service: Injected route service

    Returns:
        Ordered list of coordinates defining the route shape

    Raises:
        HTTPException: If route not found or database error occurs
    """
    try:
        shape = route_service.get_route_shape(route_id)

        if shape is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route '{route_id}' not found in GTFS database",
            )

        return map_route_shape_to_response(shape)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve route shape: {str(e)}",
        ) from e
