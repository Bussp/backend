from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.database.models import TripDB
from src.web.schemas import CreateTripRequest, RouteIdentifierSchema

from .conftest import create_user_and_login


class TestCreateTrip:
    @pytest.mark.asyncio
    async def test_create_trip_should_return_successfully_and_save_to_database(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=1,
            ),
            distance=5000,
            data=datetime.now(timezone.utc),
        )

        response = await client.post(
            "/trips/",
            json=trip_data.model_dump(mode="json"),
            headers=auth["headers"],
        )

        assert response.status_code == 201
        data = response.json()

        assert "score" in data

        result = await test_db.execute(
            select(TripDB).where(TripDB.email == user_data["email"])
        )
        trip = result.scalar_one_or_none()

        assert trip is not None
        assert trip.email == user_data["email"]
        assert trip.bus_line == "8000"
        assert trip.bus_direction == 1
        assert trip.distance == 5000
        assert trip.score == data["score"]

    @pytest.mark.asyncio
    async def test_create_trip_updates_user_score(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=1,
            ),
            distance=1000,
            data=datetime.now(timezone.utc),
        )
        second_trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=1,
            ),
            distance=2000,
            data=datetime.now(timezone.utc),
        )

        resp1 = await client.post(
            "/trips/", json=trip_data.model_dump(mode="json"), headers=auth["headers"]
        )
        assert resp1.status_code == 201
        data1 = resp1.json()
        score1 = data1["score"]

        resp2 = await client.post(
            "/trips/",
            json=second_trip_data.model_dump(mode="json"),
            headers=auth["headers"],
        )
        assert resp2.status_code == 201
        data2 = resp2.json()
        score2 = data2["score"]

        user_response = await client.get("/users/me", headers=auth["headers"])
        assert user_response.status_code == 200
        user_data_response = user_response.json()

        assert user_data_response["score"] == score1 + score2

    @pytest.mark.asyncio
    async def test_create_trip_without_authentication_fails(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=1,
            ),
            distance=1000,
            data=datetime.now(timezone.utc),
        )

        response = await client.post("/trips/", json=trip_data.model_dump(mode="json"))

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_trip_zero_distance(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="9000",
                bus_direction=2,
            ),
            distance=0,
            data=datetime.now(timezone.utc),
        )

        response = await client.post(
            "/trips/",
            json=trip_data.model_dump(mode="json"),
            headers=auth["headers"],
        )

        assert response.status_code == 201
        assert response.json()["score"] == 0

    @pytest.mark.asyncio
    async def test_create_trip_negative_distance_fails(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=1,
            ),
            distance=-1000,
            data=datetime.now(timezone.utc),
        )

        response = await client.post(
            "/trips/",
            json=trip_data.model_dump(mode="json"),
            headers=auth["headers"],
        )

        assert response.status_code == 422

        result = await test_db.execute(
            select(TripDB).where(TripDB.email == user_data["email"])
        )
        trip = result.scalar_one_or_none()
        assert trip is None

    @pytest.mark.asyncio
    async def test_create_trip_invalid_route_identifier_fails(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(
                bus_line="8000",
                bus_direction=3,
            ),
            distance=1000,
            data=datetime.now(timezone.utc),
        )

        response = await client.post(
            "/trips/",
            json=trip_data.model_dump(mode="json"),
            headers=auth["headers"],
        )

        assert response.status_code == 422

        result = await test_db.execute(
            select(TripDB).where(TripDB.email == user_data["email"])
        )
        trip = result.scalar_one_or_none()
        assert trip is None
