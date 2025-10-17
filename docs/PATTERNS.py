"""
Common Patterns and Best Practices for BusSP Application

This file provides examples of common patterns used throughout the codebase.
"""

# ============================================================================
# PATTERN 1: Dependency Injection with FastAPI
# ============================================================================

"""
Problem: How do services get their dependencies?
Solution: Use FastAPI's Depends() for automatic injection

File: src/main.py
"""

from fastapi import Depends


# Define provider functions
def get_user_repository(db=Depends(get_db)):
    return UserRepositoryAdapter(db)


def get_user_service(repo=Depends(get_user_repository)):
    return UserService(repo)


# Controllers automatically receive injected services
@router.post("/users")
async def create_user(
    request: UserCreateAccountRequest,
    service: UserService = Depends(get_user_service),  # ← Magic happens here!
):
    return await service.create_user(...)


# ============================================================================
# PATTERN 2: Repository Pattern
# ============================================================================

"""
Problem: How to access data without coupling to a specific database?
Solution: Define abstract repository interfaces (ports)

File: src/core/ports/user_repository.py
"""

from abc import ABC, abstractmethod


class UserRepository(ABC):
    """Abstract interface - can be implemented by ANY storage system"""

    @abstractmethod
    async def save_user(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        pass


# Services depend on the interface, not the implementation
class UserService:
    def __init__(self, user_repository: UserRepository):  # ← Interface, not concrete class
        self.user_repository = user_repository


"""
File: src/adapters/repositories/user_repository_adapter.py
"""


class UserRepositoryAdapter(UserRepository):
    """Concrete implementation using SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_user(self, user: User) -> User:
        user_db = map_user_domain_to_db(user)
        self.session.add(user_db)
        await self.session.flush()
        return map_user_db_to_domain(user_db)


# ============================================================================
# PATTERN 3: Mapper Pattern
# ============================================================================

"""
Problem: Different layers need different representations of the same data
Solution: Create explicit mapper functions

Why? Keeps layers decoupled. Changing one model doesn't affect others.
"""


# Web → Domain
def map_create_request_to_user(request: UserCreateAccountRequest) -> User:
    return User(
        name=request.name,
        email=request.email,
        password=request.password,
        score=0,
    )


# Domain → Web
def map_user_to_response(user: User) -> UserResponse:
    return UserResponse(
        name=user.name,
        email=user.email,
        score=user.score,
    )


# Domain → DB
def map_user_domain_to_db(user: User) -> UserDB:
    return UserDB(
        email=user.email,
        name=user.name,
        score=user.score,
        password=user.password,
    )


# DB → Domain
def map_user_db_to_domain(user_db: UserDB) -> User:
    return User(
        name=user_db.name,
        email=user_db.email,
        score=user_db.score,
        password=user_db.password,
    )


# ============================================================================
# PATTERN 4: Service Layer Pattern
# ============================================================================

"""
Problem: Where does business logic live?
Solution: Dedicated service classes in the core layer

Services orchestrate use cases and contain business rules.
"""


class TripService:
    def __init__(
        self,
        trip_repository: TripRepository,
        user_repository: UserRepository,
    ):
        self.trip_repository = trip_repository
        self.user_repository = user_repository

    async def create_trip(
        self,
        email: str,
        bus_line: str,
        bus_direction: int,
        distance: int,
        trip_date: datetime,
    ) -> Trip:
        # Step 1: Validate
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise ValueError(f"User {email} not found")

        # Step 2: Apply business logic
        score = distance // 100  # ← Business rule: 1 point per 100m

        # Step 3: Create domain entity
        trip = Trip(
            email=email,
            bus_line=bus_line,
            bus_direction=bus_direction,
            distance=distance,
            score=score,
            start_date=trip_date,
            end_date=trip_date,
        )

        # Step 4: Persist
        saved_trip = await self.trip_repository.save_trip(trip)

        # Step 5: Side effects
        await self.user_repository.add_user_score(email, score)

        return saved_trip


# ============================================================================
# PATTERN 5: Controller Pattern (Thin Controllers)
# ============================================================================

"""
Problem: What should controllers do?
Solution: Keep them thin - just HTTP handling, delegate to services

Controllers should:
✅ Validate input (Pydantic does this automatically)
✅ Call appropriate service
✅ Map domain models to API responses
✅ Handle HTTP-specific concerns (status codes, headers)

Controllers should NOT:
❌ Contain business logic
❌ Talk directly to databases
❌ Do complex calculations
"""


@router.post("/trips/", response_model=CreateTripResponse)
async def create_trip(
    request: CreateTripRequest,  # 1. Pydantic validates
    trip_service: TripService = Depends(),  # 2. Dependency injection
) -> CreateTripResponse:
    try:
        # 3. Call service (where business logic lives)
        trip = await trip_service.create_trip(
            email=request.email,
            bus_line=request.bus_line,
            bus_direction=request.bus_direction,
            distance=request.distance,
            trip_date=request.data,
        )

        # 4. Map to response
        return CreateTripResponse(score=trip.score)

    except ValueError as e:
        # 5. Handle HTTP errors
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PATTERN 6: Domain Model Pattern
# ============================================================================

"""
Problem: How to represent business entities?
Solution: Simple dataclasses with no framework dependencies

Domain models are the heart of your application.
Keep them pure and framework-agnostic!
"""

from dataclasses import dataclass


@dataclass
class User:
    """
    Domain entity representing a user.

    Pure Python - no FastAPI, no SQLAlchemy, no nothing!
    This can be used in any context: CLI, API, background jobs, etc.
    """

    name: str
    email: str
    score: int = 0
    password: str = ""


# ✅ Good: Pure Python
# ❌ Bad: Don't do this in domain models:
#   - from sqlalchemy import Column, Integer  # ← NO!
#   - from fastapi import UploadFile           # ← NO!
#   - from pydantic import BaseModel          # ← NO!


# ============================================================================
# PATTERN 7: Adapter Pattern
# ============================================================================

"""
Problem: How to integrate with external systems (APIs, databases)?
Solution: Create adapters that implement port interfaces

Adapters translate between external formats and domain models.
"""


class SpTransAdapter(SpTransPort):
    """Adapter for SPTrans API"""

    def __init__(self, api_token: str, base_url: str):
        self.api_token = api_token
        self.client = httpx.AsyncClient(base_url=base_url)

    async def get_bus_positions(self, routes: List[RouteIdentifier]) -> List[BusPosition]:
        positions = []

        for route in routes:
            # 1. Call external API
            response = await self.client.get(
                f"/Posicao/Linha", params={"codigoLinha": route.bus_line}
            )

            # 2. Parse external format
            data = response.json()
            vehicles = data.get("vs", [])

            # 3. Translate to domain models
            for vehicle in vehicles:
                position = BusPosition(
                    route=route,
                    position=Coordinate(
                        latitude=vehicle["py"] / 1_000_000,  # ← Translation
                        longitude=vehicle["px"] / 1_000_000,
                    ),
                    time_updated=datetime.fromisoformat(vehicle["ta"]),
                )
                positions.append(position)

        return positions


# ============================================================================
# PATTERN 8: Configuration Pattern
# ============================================================================

"""
Problem: How to manage configuration?
Solution: Use Pydantic Settings with environment variables

File: src/config.py
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Defaults can be overridden by environment variables
    database_url: str = "sqlite+aiosqlite:///./bussp.db"
    sptrans_api_token: str = ""
    debug: bool = False

    class Config:
        env_file = ".env"  # Reads from .env file


# Global instance
settings = Settings()

# Usage anywhere in the app:
from src.config import settings

print(settings.database_url)


# ============================================================================
# PATTERN 9: Testing with Mocks
# ============================================================================

"""
Problem: How to test business logic without infrastructure?
Solution: Create mock implementations of ports

This is the POWER of Hexagonal Architecture!
"""


class MockUserRepository(UserRepository):
    """In-memory repository for testing"""

    def __init__(self):
        self.users: dict[str, User] = {}

    async def save_user(self, user: User) -> User:
        self.users[user.email] = user
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return self.users.get(email)


# In tests:
@pytest.mark.asyncio
async def test_create_user():
    # Arrange: Use mock instead of real database
    mock_repo = MockUserRepository()
    service = UserService(mock_repo)

    # Act
    user = await service.create_user("John", "john@example.com", "pass123")

    # Assert
    assert user.name == "John"
    assert user.email == "john@example.com"
    # No database needed!


# ============================================================================
# PATTERN 10: Async/Await Pattern
# ============================================================================

"""
Problem: How to handle I/O efficiently?
Solution: Use async/await throughout the stack

All I/O operations (database, HTTP) are async for maximum performance.
"""


# Async database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Async repository
class UserRepositoryAdapter(UserRepository):
    async def save_user(self, user: User) -> User:  # ← async
        user_db = map_user_domain_to_db(user)
        self.session.add(user_db)
        await self.session.flush()  # ← await
        return map_user_db_to_domain(user_db)


# Async service
class UserService:
    async def create_user(self, name: str, email: str, password: str) -> User:
        existing = await self.user_repository.get_user_by_email(email)  # ← await
        if existing:
            raise ValueError("User exists")
        user = User(name=name, email=email, password=password)
        return await self.user_repository.save_user(user)  # ← await


# Async controller
@router.post("/users/register")
async def create_user(  # ← async
    request: UserCreateAccountRequest,
    service: UserService = Depends(),
):
    user = await service.create_user(...)  # ← await
    return map_user_to_response(user)


# ============================================================================
# ANTI-PATTERNS TO AVOID
# ============================================================================

ANTI_PATTERNS = """
❌ DON'T: Put business logic in controllers
   
   @router.post("/trips/")
   async def create_trip(...):
       score = distance // 100  # ← NO! This is business logic
       trip = Trip(...)
       # ...

✅ DO: Put business logic in services
   
   class TripService:
       async def create_trip(self, ...):
           score = distance // 100  # ← YES! Business logic in service
           # ...


❌ DON'T: Import SQLAlchemy in core layer

   # src/core/models/user.py
   from sqlalchemy import Column  # ← NO!

✅ DO: Keep core layer pure

   # src/core/models/user.py
   from dataclasses import dataclass  # ← YES!


❌ DON'T: Import domain models in database models

   # src/adapters/database/models.py
   from src.core.models.user import User  # ← NO!

✅ DO: Keep layers independent, use mappers

   # src/adapters/database/mappers.py
   def map_user_db_to_domain(user_db: UserDB) -> User:  # ← YES!


❌ DON'T: Skip type hints

   def create_user(name, email):  # ← NO!
       return User(name, email)

✅ DO: Use type hints everywhere

   def create_user(name: str, email: str) -> User:  # ← YES!
       return User(name, email)
"""

if __name__ == "__main__":
    print("Common Patterns in BusSP Application")
    print("=" * 50)
    print(ANTI_PATTERNS)
