from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters.database.connection import get_db
from ..adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from ..adapters.security.hashing import PasslibPasswordHasher
from ..adapters.security.jwt import verify_token
from ..core.models.user import User
from ..core.ports.password_hasher import PasswordHasherPort
from ..core.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_password_hasher() -> PasswordHasherPort:
    return PasslibPasswordHasher()


def get_user_service(
    db: AsyncSession = Depends(get_db),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> UserService:
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
