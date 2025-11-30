"""
Exemplo demonstrando o uso de mocks com create_autospec().

Note que o teste só depende da implementação do serviço. As implementações de
repositórios e adaptadores são simuladas, e passamos as respostas que esperamos
dessas funções que não estão sendo testadas no próprio teste. Dessa maneira,
isolamos as preocupações do teste, que passa a verificar apenas o service.
Isso faz o teste ficar mais específico, fácil de escrever e fácil de debugar.
Principalmente conforme o código cresce.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.user import User
from src.core.ports.trip_repository import TripRepository
from src.core.ports.user_repository import UserRepository
from src.core.services.trip_service import TripService

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_create_trip_calculates_score_correctly() -> None:
    """Test score calculation with autospecced mocks."""
    # Arrange
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Test User",
        email="test@example.com",
        score=0,
        password="hashed_password",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    distance = 1000

    # Act
    trip = await service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=distance,
        trip_date=datetime(2025, 10, 16, 10, 0, 0),
    )

    # Assert
    expected_score = (distance // 1000) * 77
    assert trip.score == expected_score
    assert trip.email == "test@example.com"
    assert trip.bus_line == "8000"

    user_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_awaited_once_with("test@example.com", expected_score)


@pytest.mark.asyncio
async def test_create_trip_with_pytest_mock(mocker: "MockerFixture") -> None:
    """Test using pytest-mock fixture for cleaner syntax."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Alice",
        email="alice@example.com",
        score=0,
        password="secure_hash",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    distance = 2500

    # Act
    trip = await service.create_trip(
        email="alice@example.com",
        bus_line="9000",
        bus_direction=2,
        distance=distance,
        trip_date=datetime(2025, 10, 16, 14, 30, 0),
    )

    # Assert
    expected_score = (distance // 1000) * 77
    assert trip.score == expected_score
    user_repo.add_user_score.assert_awaited_once_with("alice@example.com", expected_score)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_trip_fails_for_nonexistent_user(mocker: "MockerFixture") -> None:
    """Test error handling when user doesn't exist."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    user_repo.get_user_by_email = AsyncMock(return_value=None)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock()

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="ghost@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )

    user_repo.get_user_by_email.assert_awaited_once_with("ghost@example.com")  # type: ignore[attr-defined]
    trip_repo.save_trip.assert_not_awaited()  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_multiple_trips(mocker: "MockerFixture") -> None:
    """Test multiple sequential calls to the service."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Bob",
        email="bob@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)  # type: ignore[misc]

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act
    trip1 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=500,
        trip_date=datetime.now(),
    )

    trip2 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=2,
        distance=1500,
        trip_date=datetime.now(),
    )

    # Assert
    assert trip1.score == 0
    assert trip2.score == 77
    assert trip_repo.save_trip.await_count == 2  # type: ignore[attr-defined]
    assert user_repo.add_user_score.await_count == 2  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_any_await("bob@example.com", 0)  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_any_await("bob@example.com", 77)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_handles_repository_save_error(mocker: "MockerFixture") -> None:
    """Test error handling when repository fails."""
    # Arrange
    user_repo = mocker.create_autospec(UserRepository, instance=True)
    trip_repo = mocker.create_autospec(TripRepository, instance=True)

    test_user = User(
        name="Charlie",
        email="charlie@example.com",
        score=0,
        password="hash",
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock()
    trip_repo.save_trip = AsyncMock(side_effect=RuntimeError("Database connection lost!"))

    service = TripService(trip_repo, user_repo)  # type: ignore[arg-type]

    # Act & Assert
    with pytest.raises(RuntimeError, match="Database connection lost"):
        await service.create_trip(
            email="charlie@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_date=datetime.now(),
        )

    trip_repo.save_trip.assert_awaited_once()  # type: ignore[attr-defined]
    user_repo.add_user_score.assert_not_awaited()  # type: ignore[attr-defined]
