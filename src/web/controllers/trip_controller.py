"""
Trip controller - API endpoints for trip management.

This controller handles trip creation and scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.trip_repository_adapter import TripRepositoryAdapter
from ...adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ...core.services.trip_service import TripService
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


@router.post("/", response_model=CreateTripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: CreateTripRequest,
    trip_service: TripService = Depends(get_trip_service),
) -> CreateTripResponse:
    """
    Create a new trip and calculate score.

    Args:
        request: Trip creation request
        trip_service: Injected trip service

    Returns:
        Score earned from the trip

    Raises:
        HTTPException: If user not found or validation fails
    """
    try:
        trip = await trip_service.create_trip(
            email=request.email,
            bus_line=request.route.bus_line,
            bus_direction=request.route.bus_direction,
            distance=request.distance,
            trip_date=request.data,
        )

        return CreateTripResponse(score=trip.score)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
