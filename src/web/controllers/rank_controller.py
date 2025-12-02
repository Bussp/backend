"""
Rank controller - API endpoints for user rankings.

This controller handles queries for user rankings and leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ...core.models.user import User
from ...core.services.score_service import ScoreService
from ..auth import get_current_user
from ..mappers import map_user_domain_list_to_response
from ..schemas import GlobalRankingResponse, UserRankingResponse

router = APIRouter(prefix="/rank", tags=["ranking"])


def get_score_service(db: AsyncSession = Depends(get_db)) -> ScoreService:
    """
    Dependency that provides a ScoreService instance.

    Args:
        db: Database session

    Returns:
        Configured ScoreService instance
    """
    user_repo = UserRepositoryAdapter(db)
    return ScoreService(user_repo)


@router.get("/user", response_model=UserRankingResponse)
async def get_user_ranking(
    score_service: ScoreService = Depends(get_score_service),
    current_user: User = Depends(get_current_user),
) -> UserRankingResponse:
    position = await score_service.get_user_ranking(current_user.email)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserRankingResponse(position=position)


@router.get("/global", response_model=GlobalRankingResponse)
async def get_global_ranking(
    score_service: ScoreService = Depends(get_score_service),
    current_user: User = Depends(get_current_user),
) -> GlobalRankingResponse:
    """
    Get the global user ranking.

    Args:
        score_service: Injected score service

    Returns:
        List of all users ordered by score
    """
    users = await score_service.get_global_ranking()
    user_responses = map_user_domain_list_to_response(users)

    return GlobalRankingResponse(users=user_responses)
