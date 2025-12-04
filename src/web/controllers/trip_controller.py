"""
Trip controller - API endpoints for trip management.

This controller handles trip creation and scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.trip_repository_adapter import TripRepositoryAdapter
from ...adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ...core.models.bus import RouteIdentifier
from ...core.models.user import User
from ...core.services.trip_service import TripService
from ..auth import get_current_user
from ..schemas import CreateTripRequest, CreateTripResponse

router = APIRouter(prefix="/trips", tags=["trips"])


def get_trip_service(db: AsyncSession = Depends(get_db)) -> TripService:
    """
    Dependency that provides a TripService instance.

    Args:
        db: Database session

    Returns:
        Configured TripService instance
    """
    trip_repo = TripRepositoryAdapter(db)
    user_repo = UserRepositoryAdapter(db)
    return TripService(trip_repo, user_repo)


# NOTE: Having `current_user: User = Depends(get_current_user)` as a dependency
# makes this endpoint only accessible to authenticated users (requires valid JWT token).
@router.post("/", response_model=CreateTripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: CreateTripRequest,
    trip_service: TripService = Depends(get_trip_service),
    current_user: User = Depends(get_current_user),
) -> CreateTripResponse:
    """
    Create a new trip and calculate score.

    Args:
        request: Trip creation request
        trip_service: Injected trip service
        current_user: Authenticated user (from JWT token)

    Returns:
        Score earned from the trip

    Raises:
        HTTPException: If user not found or validation fails
    """
    try:
        route = RouteIdentifier(
            bus_line=request.route.bus_line,
            bus_direction=request.route.bus_direction,
        )
        trip = await trip_service.create_trip(
            email=current_user.email,
            route=route,
            distance=request.distance,
            trip_date=request.data,
        )

        return CreateTripResponse(score=trip.score)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
