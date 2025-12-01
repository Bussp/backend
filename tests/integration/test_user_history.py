from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.schemas import (
    CreateTripRequest,
    HistoryRequest,
    HistoryResponse,
    RouteIdentifierSchema,
)

from .conftest import create_user_and_login


class TestUserHistory:
    @pytest.mark.asyncio
    async def test_get_user_history_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_dates: list[datetime] = [
            datetime(2025, 11, 1, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 11, 15, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 11, 29, 18, 0, 0, tzinfo=timezone.utc),
        ]

        scores: list[int] = []
        for i, trip_date in enumerate(trip_dates):
            trip_request = CreateTripRequest(
                email=user_data["email"],
                route=RouteIdentifierSchema(bus_line=f"800{i}", bus_direction=1),
                distance=(i + 1) * 1000,
                data=trip_date,
            )
            response = await client.post(
                "/trips/",
                json=trip_request.model_dump(mode="json"),
                headers=auth["headers"],
            )
            scores.append(response.json()["score"])

        history_request = HistoryRequest(email=user_data["email"])
        response = await client.post(
            "/history/",
            json=history_request.model_dump(),
            headers=auth["headers"],
        )

        assert response.status_code == 200
        history_response = HistoryResponse.model_validate(response.json())

        assert len(history_response.trips) == 3

        for trip in history_response.trips:
            assert isinstance(trip.date, datetime)
            assert isinstance(trip.score, int)

        assert sorted(scores) == sorted([trip.score for trip in history_response.trips])

    @pytest.mark.asyncio
    async def test_get_user_history_returns_empty_when_no_trips(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "secure_password_123",
        }

        auth = await create_user_and_login(client, user_data)

        history_request = HistoryRequest(email=user_data["email"])

        response = await client.post(
            "/history/",
            json=history_request.model_dump(),
            headers=auth["headers"],
        )

        assert response.status_code == 200
        history_response = HistoryResponse.model_validate(response.json())
        assert isinstance(history_response.trips, list)
        assert len(history_response.trips) == 0

    @pytest.mark.asyncio
    async def test_get_user_history_without_authentication_fails(
        self,
        client: AsyncClient,
    ) -> None:
        history_request = HistoryRequest(email="test@example.com")
        response = await client.post("/history/", json=history_request.model_dump())

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_history_includes_correct_dates(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        auth = await create_user_and_login(client, user_data)

        specific_date: datetime = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        trip_request = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
            distance=1000,
            data=specific_date,
        )
        await client.post(
            "/trips/",
            json=trip_request.model_dump(mode="json"),
            headers=auth["headers"],
        )

        history_request = HistoryRequest(email=user_data["email"])
        response = await client.post(
            "/history/",
            json=history_request.model_dump(),
            headers=auth["headers"],
        )

        assert response.status_code == 200
        history_response = HistoryResponse.model_validate(response.json())

        trip_date = history_response.trips[0].date
        assert trip_date.year == 2025
        assert trip_date.month == 6
        assert trip_date.day == 15
