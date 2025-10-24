"""
Route controller - API endpoints for bus routes and positions.

This controller handles queries for real-time bus information.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ...adapters.external.sptrans_adapter import SpTransAdapter
from ...config import settings
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
        )
