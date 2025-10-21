"""
Main application entry point.

This module initializes the FastAPI application and wires up all dependencies
using the Dependency Injection pattern.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .adapters.database.connection import create_tables, get_db
from .adapters.external.sptrans_adapter import SpTransAdapter
from .adapters.repositories.history_repository_adapter import (
    UserHistoryRepositoryAdapter,
)
from .adapters.repositories.trip_repository_adapter import TripRepositoryAdapter
from .adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from .config import settings
from .core.ports.bus_provider_port import BusProviderPort
from .core.ports.history_repository import UserHistoryRepository
from .core.ports.trip_repository import TripRepository
from .core.ports.user_repository import UserRepository
from .core.services.history_service import HistoryService
from .core.services.route_service import RouteService
from .core.services.score_service import ScoreService
from .core.services.trip_service import TripService
from .core.services.user_service import UserService
from .web.controllers import (
    history_controller,
    rank_controller,
    route_controller,
    trip_controller,
    user_controller,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup: Create database tables
    await create_tables()
    yield
    # Shutdown: cleanup if needed


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A gamified public transport tracking system with Hexagonal Architecture",
    version="1.0.0",
    lifespan=lifespan,
)


# ===== Dependency Injection Providers =====


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """
    Provide UserRepository implementation.

    Args:
        db: Database session

    Returns:
        UserRepository adapter instance
    """
    return UserRepositoryAdapter(db)


def get_trip_repository(
    db: AsyncSession = Depends(get_db),
) -> TripRepository:
    """
    Provide TripRepository implementation.

    Args:
        db: Database session

    Returns:
        TripRepository adapter instance
    """
    return TripRepositoryAdapter(db)


def get_history_repository(
    db: AsyncSession = Depends(get_db),
) -> UserHistoryRepository:
    """
    Provide UserHistoryRepository implementation.

    Args:
        db: Database session

    Returns:
        UserHistoryRepository adapter instance
    """
    return UserHistoryRepositoryAdapter(db)


def get_bus_provider() -> BusProviderPort:
    """
    Provide BusProviderPort implementation.

    Returns:
        BusProviderPort adapter instance
    """
    return SpTransAdapter(
        api_token=settings.sptrans_api_token,
        base_url=settings.sptrans_base_url,
    )


# ===== Service Providers =====


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """
    Provide UserService instance.

    Args:
        user_repository: User repository implementation

    Returns:
        UserService instance
    """
    return UserService(user_repository)


def get_trip_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> TripService:
    """
    Provide TripService instance.

    Args:
        trip_repository: Trip repository implementation
        user_repository: User repository implementation

    Returns:
        TripService instance
    """
    return TripService(trip_repository, user_repository)


def get_route_service(
    bus_provider: BusProviderPort = Depends(get_bus_provider),
) -> RouteService:
    """
    Provide RouteService instance.

    Args:
        bus_provider: Bus provider port implementation

    Returns:
        RouteService instance
    """
    return RouteService(bus_provider)


def get_score_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ScoreService:
    """
    Provide ScoreService instance.

    Args:
        user_repository: User repository implementation

    Returns:
        ScoreService instance
    """
    return ScoreService(user_repository)


def get_history_service(
    history_repository: UserHistoryRepository = Depends(get_history_repository),
) -> HistoryService:
    """
    Provide HistoryService instance.

    Args:
        history_repository: History repository implementation

    Returns:
        HistoryService instance
    """
    return HistoryService(history_repository)


# ===== Override Dependencies in Controllers =====

# Register dependency overrides for controllers
app.dependency_overrides[UserService] = get_user_service
app.dependency_overrides[TripService] = get_trip_service
app.dependency_overrides[RouteService] = get_route_service
app.dependency_overrides[ScoreService] = get_score_service
app.dependency_overrides[HistoryService] = get_history_service


# ===== Include Routers =====

app.include_router(user_controller.router)
app.include_router(trip_controller.router)
app.include_router(route_controller.router)
app.include_router(rank_controller.router)
app.include_router(history_controller.router)


# ===== Root Endpoint =====


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Welcome to BusSP API",
        "description": "Gamified public transport tracking system",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
