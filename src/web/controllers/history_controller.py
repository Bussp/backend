from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.history_repository_adapter import (
    UserHistoryRepositoryAdapter,
)
from ...core.models.user import User
from ...core.services.history_service import HistoryService
from ..auth import get_current_user
from ..schemas import HistoryResponse, TripHistoryEntry

router = APIRouter(prefix="/history", tags=["history"])


def get_history_service(db: AsyncSession = Depends(get_db)) -> HistoryService:
    """
    Dependency that provides a HistoryService instance.

    Args:
        db: Database session

    Returns:
        Configured HistoryService instance
    """
    history_repo = UserHistoryRepositoryAdapter(db)
    return HistoryService(history_repo)


# NOTE: Having `current_user: User = Depends(get_current_user)` as a dependency
# makes this endpoint only accessible to authenticated users (requires valid JWT token).
@router.get("/", response_model=HistoryResponse)
async def get_user_history(
    history_service: HistoryService = Depends(get_history_service),
    current_user: User = Depends(get_current_user),
) -> HistoryResponse:
    """
    Get a user's trip history summary.

    Args:
        history_service: Injected history service
        current_user: Authenticated user (from JWT token)

    Returns:
        User's trip history with dates and scores (empty list if no history)
    """
    dates, scores = await history_service.get_user_history_summary(current_user.email)

    # Combine dates and scores into trip entries (returns empty list if no history)
    trips = [
        TripHistoryEntry(date=date, score=score) for date, score in zip(dates, scores, strict=False)
    ]

    return HistoryResponse(trips=trips)
