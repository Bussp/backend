"""
Rank controller - API endpoints for user rankings.

This controller handles queries for user rankings and leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.services.score_service import ScoreService
from ..mappers import map_user_domain_list_to_response
from ..schemas import GlobalRankingResponse, UserRankingRequest, UserRankingResponse

router = APIRouter(prefix="/rank", tags=["ranking"])


@router.post("/user", response_model=UserRankingResponse)
async def get_user_ranking(
    request: UserRankingRequest,
    score_service: ScoreService = Depends(),
) -> UserRankingResponse:
    """
    Get a user's position in the global ranking.

    Args:
        request: Request with user email
        score_service: Injected score service

    Returns:
        User's rank position

    Raises:
        HTTPException: If user not found
    """
    position = await score_service.get_user_ranking(request.email)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserRankingResponse(position=position)


@router.get("/global", response_model=GlobalRankingResponse)
async def get_global_ranking(
    score_service: ScoreService = Depends(),
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
