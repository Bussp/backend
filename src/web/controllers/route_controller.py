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
    map_bus_route_schema_list_to_domain,
    map_route_shape_to_response,
)
from ..schemas import (
    BusPositionsRequest,
    BusPositionsResponse,
    RouteSearchResponse,
    RouteShapeResponse,
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


@router.post("/positions", response_model=BusPositionsResponse)
async def get_bus_positions(
    request: BusPositionsRequest,
    route_service: RouteService = Depends(get_route_service),
    current_user: User = Depends(get_current_user),
) -> BusPositionsResponse:
    """
    Get real-time bus positions for specified routes.

    Args:
        request: Request containing list of routes.
        route_service: Injected route service.
        current_user: Authenticated user.

    Returns:
        List of bus positions with route identifiers.

    Raises:
        HTTPException: If fetching positions fails.
    """
    try:
        bus_routes = map_bus_route_schema_list_to_domain(request.routes)
        positions: list[BusPosition] = await route_service.get_bus_positions(bus_routes)
        position_schemas = map_bus_position_list_to_schema(positions)
        return BusPositionsResponse(buses=position_schemas)

    except Exception as e:
        detail: str = f"Failed to retrieve bus positions: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e


@router.get("/shape/{route_id}", response_model=RouteShapeResponse)
async def get_route_shape(
    route_id: str,
    route_service: RouteService = Depends(get_route_service),
    current_user: User = Depends(get_current_user),
) -> RouteShapeResponse:
    """
    Get the geographic shape (coordinates) of a route from GTFS data.

    Args:
        route_id: Route identifier (e.g., "1012-10").
        route_service: Injected route service.
        current_user: Authenticated user.

    Returns:
        Ordered list of coordinates defining the route shape.

    Raises:
        HTTPException: If route not found or database error occurs.
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
