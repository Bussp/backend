"""
Route controller - API endpoints for bus routes and positions.

This controller handles queries for real-time bus information and route shapes.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...adapters.external.sptrans_adapter import SpTransAdapter
from ...adapters.repositories.gtfs_repository_adapter import GTFSRepositoryAdapter
from ...config import settings
from ...core.models.bus import BusPosition, BusRoute, RouteIdentifier
from ...core.services.route_service import RouteService
from ..mappers import (
    map_bus_position_list_to_schema,
    map_route_identifier_schema_to_domain,
    map_route_shape_to_response,
)
from ..schemas import (
    BusPositionsRequest,
    BusPositionsResponse,
    BusRouteSchema,
    BusRoutesDetailsRequest,
    BusRoutesDetailsResponse,
    RouteIdentifierSchema,
    RouteShapeResponse
)

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


@router.post("/details", response_model=BusRoutesDetailsResponse)
async def get_route_details_endpoint(
    request: BusRoutesDetailsRequest,
    route_service: RouteService = Depends(get_route_service),
) -> BusRoutesDetailsResponse:
    """
    Resolve, para cada linha solicitada, as rotas concretas do provedor
    (por exemplo, diferentes variantes/direções internamente).

    Entrada: lista de RouteIdentifierSchema (apenas bus_line).
    Saída: lista "achatada" de BusRouteSchema (route_id + bus_line).
    """
    try:
        # Schemas -> domínio (RouteIdentifier)
        route_identifiers: list[RouteIdentifier] = [
            map_route_identifier_schema_to_domain(route_schema)
            for route_schema in request.routes
        ]

        bus_routes: list[BusRoute] = []

        for route_identifier in route_identifiers:
            # O service retorna uma lista de BusRoute
            resolved_routes: list[BusRoute] = await route_service.get_route_details(
                route_identifier
            )
            bus_routes.extend(resolved_routes)

        # Domínio -> schemas
        route_schemas: list[BusRouteSchema] = [
            BusRouteSchema(
                route_id=bus_route.route_id,
                route=RouteIdentifierSchema(
                    bus_line=bus_route.route.bus_line,
                ),
            )
            for bus_route in bus_routes
        ]

        return BusRoutesDetailsResponse(routes=route_schemas)

    except Exception as e:  # caminho de erro genérico
        detail: str = f"Failed to retrieve route details: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e


@router.post("/positions", response_model=BusPositionsResponse)
async def get_bus_positions(
    request: BusPositionsRequest,
    route_service: RouteService = Depends(get_route_service),
) -> BusPositionsResponse:
    """
    Recupera as posições dos ônibus para as rotas já resolvidas.

    Entrada: lista de BusRouteSchema (tipicamente saída de /routes/details).
    Saída: lista de BusPositionSchema.
    """
    try:
        all_positions: list[BusPosition] = []

        for route_schema in request.routes:
            # Schema -> domínio (BusRoute)
            route_identifier = RouteIdentifier(
                bus_line=route_schema.route.bus_line,
                bus_direction=1,  # direção default; SPTrans /Linha/Buscar não usa mais isso
            )

            bus_route = BusRoute(
                route_id=route_schema.route_id,
                route=route_identifier,
            )

            route_positions: list[BusPosition] = await route_service.get_bus_positions(
                bus_route
            )
            all_positions.extend(route_positions)

        # Domínio -> schemas
        position_schemas = map_bus_position_list_to_schema(all_positions)
        return BusPositionsResponse(buses=position_schemas)

    except Exception as e:  # caminho de erro genérico
        detail: str = f"Failed to retrieve bus positions: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
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
