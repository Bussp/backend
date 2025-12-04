"""
Integration tests configuration and fixtures.

This module provides shared fixtures for all integration tests,
including test database setup, test client, and helper functions.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.database.connection import Base, get_db
from src.adapters.database.models import UserDB
from src.adapters.security.hashing import PasslibPasswordHasher
from src.main import app

IN_MEMORY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    IN_MEMORY_TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database tables before each test and drop them after.

    Yields:
        AsyncSession: Test database session
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    app.dependency_overrides.clear()


@pytest.fixture
async def client(
    test_db: AsyncSession,
    set_sptrans_api_token: None,  # through this dependency we ensure the fake token is set
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client.

    Args:
        test_db: Test database session (ensures DB is set up)

    Yields:
        AsyncClient: HTTP client for testing
    """
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def set_sptrans_api_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Set a fake SPTrans API token for testing.

    This patches the settings object directly since it's already instantiated
    at module load time. Patching the environment variable alone won't work
    because settings.sptrans_api_token is already resolved.
    """
    monkeypatch.setattr(
        "src.config.settings.sptrans_api_token",
        "fake-test-token",
    )


async def create_user_and_login(
    client: AsyncClient,
    user_data: dict[str, str],
) -> dict[str, Any]:
    """
    Helper to create a user and login, returning token info.

    Args:
        client: HTTP client
        user_data: User registration data

    Returns:
        dict: Contains access_token and user info
    """
    # Register user
    await client.post("/users/register", json=user_data)

    # Login
    login_response = await client.post(
        "/users/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    token_data = login_response.json()

    return {
        "access_token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
        "user": user_data,
    }


async def create_test_user_in_db(
    session: AsyncSession,
    email: str,
    score: int = 0,
    password: str = "password123",
) -> UserDB:
    """
    Helper to create a user directly in the database.

    Args:
        session: Database session
        email: User email
        score: User score
        password: User password

    Returns:
        UserDB: Created user object
    """
    hasher = PasslibPasswordHasher()
    hashed_password = hasher.hash(password)

    user = UserDB(
        name=email.split("@")[0],
        email=email,
        password=hashed_password,
        score=score,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
