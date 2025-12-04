"""
Route controller - API endpoints for bus routes and positions.

This controller handles queries for real-time bus information and route shapes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...adapters.external.sptrans_adapter import SpTransAdapter
from ...adapters.repositories.gtfs_repository_adapter import GTFSRepositoryAdapter
from ...config import settings
from ...core.models.bus import BusPosition, BusRoute
from ...core.models.user import User
from ...core.services.route_service import RouteService
from ..auth import get_current_user
from ..mappers import (
    map_bus_position_list_to_schema,
    map_bus_route_domain_list_to_schema,
    map_bus_route_request_list,
    map_route_identifier_schema_to_domain,
    map_route_shapes_to_response,
)
from ..schemas import (
    BusPositionsRequest,
    BusPositionsResponse,
    RouteSearchResponse,
    RouteShapesRequest,
    RouteShapesResponse,
)

router = APIRouter(prefix="/routes", tags=["routes"])


def get_route_service() -> RouteService:
    """
    Dependency that provides a RouteService instance.

    Returns:
        Configured RouteService instance.
    """
    bus_provider = SpTransAdapter(
        api_token=settings.sptrans_api_token,
        base_url=settings.sptrans_base_url,
    )
    gtfs_repository = GTFSRepositoryAdapter()
    return RouteService(bus_provider, gtfs_repository)


@router.get("/search", response_model=RouteSearchResponse)
async def search_routes_endpoint(
    query: str = Query(..., min_length=1, description="Search term for routes"),
    route_service: RouteService = Depends(get_route_service),
    current_user: User = Depends(get_current_user),
) -> RouteSearchResponse:
    """
    Search for bus routes matching a query string.

    Args:
        query: Search term (e.g., "809" or "Vila Nova Conceição").
        route_service: Injected route service.
        current_user: Authenticated user.

    Returns:
        List of matching routes with provider IDs.

    Raises:
        HTTPException: If search fails.
    """
    try:
        bus_routes: list[BusRoute] = await route_service.search_routes(query)
        route_schemas = map_bus_route_domain_list_to_schema(bus_routes)
        return RouteSearchResponse(routes=route_schemas)

    except Exception as e:
        detail: str = f"Failed to search routes: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e


# NOTE: Having `current_user: User = Depends(get_current_user)` as a dependency
# makes this endpoint only accessible to authenticated users (requires valid JWT token).
@router.post("/positions", response_model=BusPositionsResponse)
async def get_bus_positions(
    request: BusPositionsRequest,
    route_service: RouteService = Depends(get_route_service),
    current_user: User = Depends(get_current_user),
) -> BusPositionsResponse:
    """
    Get real-time bus positions for specified routes.

    Args:
        request: Request containing list of route_ids.
        route_service: Injected route service.
        current_user: Authenticated user.

    Returns:
        List of bus positions with route_id.

    Raises:
        HTTPException: If fetching positions fails.
    """
    try:
        # Extract route_ids from request
        route_ids = map_bus_route_request_list(request.routes)

        positions: list[BusPosition] = await route_service.get_bus_positions(route_ids)
        position_schemas = map_bus_position_list_to_schema(positions)
        return BusPositionsResponse(buses=position_schemas)

    except Exception as e:
        detail: str = f"Failed to retrieve bus positions: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e


# NOTE: Having `current_user: User = Depends(get_current_user)` as a dependency
# makes this endpoint only accessible to authenticated users (requires valid JWT token).
@router.post("/shapes", response_model=RouteShapesResponse)
async def get_route_shapes(
    request: RouteShapesRequest,
    route_service: RouteService = Depends(get_route_service),
    current_user: User = Depends(get_current_user),
) -> RouteShapesResponse:
    """
    Get the geographic shapes (coordinates) for multiple routes from GTFS data.

    Args:
        request: Request containing list of route identifiers (bus_line and direction)
        route_service: Injected route service

    Returns:
        List of route shapes with ordered coordinates

    Raises:
        HTTPException: If database error occurs
    """
    try:
        route_identifiers = [
            map_route_identifier_schema_to_domain(route_schema) for route_schema in request.routes
        ]

        shapes = route_service.get_route_shapes(route_identifiers)

        shape_responses = map_route_shapes_to_response(shapes)
        return RouteShapesResponse(shapes=shape_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve route shapes: {str(e)}",
        ) from e
