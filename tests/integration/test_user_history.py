from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from src.web.schemas import (
    CreateTripRequest,
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
            datetime(2025, 11, 1, 8, 0, 0, tzinfo=UTC),
            datetime(2025, 11, 15, 12, 0, 0, tzinfo=UTC),
            datetime(2025, 11, 29, 18, 0, 0, tzinfo=UTC),
        ]

        scores: list[int] = []
        for i, trip_datetime in enumerate(trip_dates):
            trip_request = CreateTripRequest(
                route=RouteIdentifierSchema(bus_line=f"800{i}", bus_direction=1),
                distance=(i + 1) * 1000,
                trip_datetime=trip_datetime,
            )
            response = await client.post(
                "/trips/",
                json=trip_request.model_dump(mode="json"),
                headers=auth["headers"],
            )
            scores.append(response.json()["score"])

        response = await client.get(
            "/history/",
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

        response = await client.get(
            "/history/",
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
        response = await client.get("/history/")

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

        specific_date: datetime = datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC)
        trip_request = CreateTripRequest(
            route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
            distance=1000,
            trip_datetime=specific_date,
        )
        await client.post(
            "/trips/",
            json=trip_request.model_dump(mode="json"),
            headers=auth["headers"],
        )

        response = await client.get(
            "/history/",
            headers=auth["headers"],
        )

        assert response.status_code == 200
        history_response = HistoryResponse.model_validate(response.json())

        trip_datetime = history_response.trips[0].date
        assert trip_datetime.year == 2025
        assert trip_datetime.month == 6
        assert trip_datetime.day == 15

    @pytest.mark.asyncio
    async def test_get_history_includes_route_identifier(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        auth = await create_user_and_login(client, user_data)

        bus_line = "8000"
        bus_direction = 2
        trip_request = CreateTripRequest(
            route=RouteIdentifierSchema(bus_line=bus_line, bus_direction=bus_direction),
            distance=5000,
            trip_datetime=datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC),
        )
        await client.post(
            "/trips/",
            json=trip_request.model_dump(mode="json"),
            headers=auth["headers"],
        )

        response = await client.get(
            "/history/",
            headers=auth["headers"],
        )

        assert response.status_code == 200
        history_response = HistoryResponse.model_validate(response.json())

        assert len(history_response.trips) == 1
        assert history_response.trips[0].route.bus_line == bus_line
        assert history_response.trips[0].route.bus_direction == bus_direction
