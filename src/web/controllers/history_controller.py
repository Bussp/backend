"""
History controller - API endpoints for user trip history.

This controller handles queries for user trip history.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.history_repository_adapter import (
    UserHistoryRepositoryAdapter,
)
from ...core.models.user import User
from ...core.services.history_service import HistoryService
from ..schemas import HistoryRequest, HistoryResponse, TripHistoryEntry

router = APIRouter(prefix="/history", tags=["history"])

# Import get_current_user from user_controller to avoid circular imports
from .user_controller import get_current_user  # noqa: E402


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


@router.post("/", response_model=HistoryResponse)
async def get_user_history(
    request: HistoryRequest,
    history_service: HistoryService = Depends(get_history_service),
    current_user: User = Depends(get_current_user),
) -> HistoryResponse:
    """
    Get a user's trip history summary.

    Args:
        request: Request with user email
        history_service: Injected history service
        current_user: Authenticated user (from JWT token)

    Returns:
        User's trip history with dates and scores (empty list if no history)
    """
    dates, scores = await history_service.get_user_history_summary(request.email)

    # Combine dates and scores into trip entries (returns empty list if no history)
    trips = [
        TripHistoryEntry(date=date, score=score) for date, score in zip(dates, scores, strict=False)
    ]

    return HistoryResponse(trips=trips)
