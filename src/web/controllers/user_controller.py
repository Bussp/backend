"""
User controller - API endpoints for user management.

This controller handles user registration and authentication.
It follows the pattern: Request -> Map to Domain -> Service -> Map to Response
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ...adapters.security.jwt import create_access_token
from ...core.models.user import User
from ...core.services.user_service import UserService
from ..auth import get_current_user, get_user_service
from ..mappers import map_user_domain_to_response
from ..schemas import (
    TokenResponse,
    UserCreateAccountRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    request: UserCreateAccountRequest,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Create a new user account.

    Args:
        request: User creation request with name, email, and password
        user_service: Injected user service

    Returns:
        Created user information

    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        user = await user_service.create_user(
            name=request.name,
            email=request.email,
            password=request.password,
        )

        return map_user_domain_to_response(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """
    Authenticate a user and return JWT token.

    Args:
        request: Login request with username (email) and password
        user_service: Injected user service

    Returns:
        JWT access token if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    user = await user_service.login_user(
        email=request.username,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, token_type="bearer")


# NOTE: Having `current_user: User = Depends(get_current_user)` as a dependency
# makes this endpoint only accessible to authenticated users (requires valid JWT token).
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return map_user_domain_to_response(current_user)
