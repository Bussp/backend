"""
User controller - API endpoints for user management.

This controller handles user registration and authentication.
It follows the pattern: Request -> Map to Domain -> Service -> Map to Response
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ...core.services.user_service import UserService
from ..mappers import map_user_domain_to_response
from ..schemas import UserCreateAccountRequest, UserLoginRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency that provides a UserService instance.

    Args:
        db: Database session

    Returns:
        Configured UserService instance
    """
    user_repo = UserRepositoryAdapter(db)
    return UserService(user_repo)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
        # In production, hash the password before passing to service
        # For now, we pass it as-is for simplicity
        user = await user_service.create_user(
            name=request.name,
            email=request.email,
            password=request.password,  # Should be hashed
        )

        return map_user_domain_to_response(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=UserResponse)
async def login_user(
    request: UserLoginRequest,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Authenticate a user.

    Args:
        request: Login request with email and password
        user_service: Injected user service

    Returns:
        User information if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    # In production, compare hashed password
    user = await user_service.login_user(
        email=request.email,
        password=request.password,  # Should be hashed
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return map_user_domain_to_response(user)


@router.get("/{email}", response_model=UserResponse)
async def get_user(
    email: str,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get user information by email.

    Args:
        email: User's email address
        user_service: Injected user service

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    user = await user_service.get_user(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return map_user_domain_to_response(user)
