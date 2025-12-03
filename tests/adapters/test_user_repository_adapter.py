"""
Tests for UserRepositoryAdapter - SQLAlchemy implementation of UserRepository.

These tests verify the repository adapter layer using an in-memory SQLite database.
"""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.database.models import Base
from src.adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from src.core.models.user import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_save_user_success(db_session: AsyncSession) -> None:
    """Test saving a new user to the database."""
    
    repository = UserRepositoryAdapter(db_session)
    user = User(
        name="John Doe",
        email="john@example.com",
        password="hashed_password",
        score=0,
    )

    
    result = await repository.save_user(user)
    await db_session.commit()

    
    assert result.name == "John Doe"
    assert result.email == "john@example.com"
    assert result.password == "hashed_password"
    assert result.score == 0


@pytest.mark.asyncio
async def test_save_user_duplicate_email(db_session: AsyncSession) -> None:
    """Test saving a user with duplicate email raises error."""
    
    repository = UserRepositoryAdapter(db_session)
    user1 = User(
        name="John Doe",
        email="john@example.com",
        password="hashed_password",
        score=0,
    )
    user2 = User(
        name="Jane Doe",
        email="john@example.com",
        password="different_password",
        score=10,
    )

    
    await repository.save_user(user1)
    await db_session.commit()

    
    with pytest.raises(ValueError, match="User with email john@example.com already exists"):
        await repository.save_user(user2)


@pytest.mark.asyncio
async def test_get_user_by_email_found(db_session: AsyncSession) -> None:
    """Test retrieving an existing user by email."""
    
    repository = UserRepositoryAdapter(db_session)
    user = User(
        name="Alice Smith",
        email="alice@example.com",
        password="hashed_password",
        score=50,
    )
    await repository.save_user(user)
    await db_session.commit()

    
    result = await repository.get_user_by_email("alice@example.com")

    
    assert result is not None
    assert result.name == "Alice Smith"
    assert result.email == "alice@example.com"
    assert result.score == 50


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession) -> None:
    """Test retrieving a non-existent user returns None."""
    
    repository = UserRepositoryAdapter(db_session)

    
    result = await repository.get_user_by_email("nonexistent@example.com")

    
    assert result is None


@pytest.mark.asyncio
async def test_get_all_users_ordered_by_score(db_session: AsyncSession) -> None:
    """Test retrieving all users ordered by score (descending)."""
    
    repository = UserRepositoryAdapter(db_session)

    users = [
        User(name="User1", email="user1@example.com", password="pass", score=10),
        User(name="User2", email="user2@example.com", password="pass", score=100),
        User(name="User3", email="user3@example.com", password="pass", score=50),
    ]

    for user in users:
        await repository.save_user(user)
    await db_session.commit()

    
    result = await repository.get_all_users_ordered_by_score()

    
    assert len(result) == 3
    assert result[0].email == "user2@example.com"  # score=100
    assert result[0].score == 100
    assert result[1].email == "user3@example.com"  # score=50
    assert result[1].score == 50
    assert result[2].email == "user1@example.com"  # score=10
    assert result[2].score == 10


@pytest.mark.asyncio
async def test_get_all_users_empty(db_session: AsyncSession) -> None:
    """Test retrieving all users when database is empty."""
    
    repository = UserRepositoryAdapter(db_session)

    
    result = await repository.get_all_users_ordered_by_score()

    
    assert result == []


@pytest.mark.asyncio
async def test_add_user_score_success(db_session: AsyncSession) -> None:
    """Test adding points to a user's score."""
    
    repository = UserRepositoryAdapter(db_session)
    user = User(
        name="Bob",
        email="bob@example.com",
        password="hashed_password",
        score=10,
    )
    await repository.save_user(user)
    await db_session.commit()

    
    result = await repository.add_user_score("bob@example.com", 25)
    await db_session.commit()

    
    assert result.score == 35

    # Verify in database
    updated_user = await repository.get_user_by_email("bob@example.com")
    assert updated_user is not None
    assert updated_user.score == 35


@pytest.mark.asyncio
async def test_add_user_score_user_not_found(db_session: AsyncSession) -> None:
    """Test adding score to non-existent user raises error."""
    
    repository = UserRepositoryAdapter(db_session)

    with pytest.raises(ValueError, match="User with email nonexistent@example.com not found"):
        await repository.add_user_score("nonexistent@example.com", 10)


@pytest.mark.asyncio
async def test_add_user_score_multiple_times(db_session: AsyncSession) -> None:
    """Test adding points to a user's score multiple times."""
    
    repository = UserRepositoryAdapter(db_session)
    user = User(
        name="Charlie",
        email="charlie@example.com",
        password="hashed_password",
        score=0,
    )
    await repository.save_user(user)
    await db_session.commit()

    
    await repository.add_user_score("charlie@example.com", 10)
    await db_session.commit()
    await repository.add_user_score("charlie@example.com", 20)
    await db_session.commit()
    result = await repository.add_user_score("charlie@example.com", 15)
    await db_session.commit()

    
    assert result.score == 45
