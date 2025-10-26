"""
User controller - API endpoints for user management.

This controller handles user registration and authentication.
It follows the pattern: Request -> Map to Domain -> Service -> Map to Response
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...adapters.database.connection import get_db
from ...adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ...adapters.security.hashing import PasslibPasswordHasher
from ...adapters.security.jwt import create_access_token, verify_token
from ...core.models.user import User
from ...core.ports.password_hasher import PasswordHasherPort
from ...core.services.user_service import UserService
from ..mappers import map_user_domain_to_response
from ..schemas import (
    TokenResponse,
    UserCreateAccountRequest,
    UserLoginRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_password_hasher() -> PasswordHasherPort:
    """Dependency that provides a password hasher implementation."""
    return PasslibPasswordHasher()


def get_user_service(
    db: AsyncSession = Depends(get_db),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> UserService:
    """
    Dependency that provides a UserService instance.

    Args:
        db: Database session

    Returns:
        Configured UserService instance
    """
    user_repo = UserRepositoryAdapter(db)
    return UserService(user_repo, password_hasher)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = await user_service.get_user(email)
    if user is None:
        raise credentials_exception

    return user


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
        )


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
    # OAuth2PasswordRequestForm uses 'username' field, which we treat as email
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

    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's information.

    This is a protected route that requires a valid JWT token.

    Args:
        current_user: Current authenticated user from token

    Returns:
        Current user's information
    """
    return map_user_domain_to_response(current_user)


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
