from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.schemas import CreateTripRequest, RouteIdentifierSchema

from .conftest import create_test_user_in_db, create_user_and_login

class TestUserRankPosition:
    @pytest.mark.asyncio
    async def test_get_user_rank_position_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        request_data = {"email": user_data["email"]}
        response = await client.post(
            "/rank/user",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()

        assert "position" in data
        assert data["position"] == 1

    @pytest.mark.asyncio
    async def test_get_user_rank_position_with_multiple_users(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        await create_test_user_in_db(test_db, "top@example.com", score=1000)
        await create_test_user_in_db(test_db, "middle@example.com", score=500)
        await create_test_user_in_db(test_db, "bottom@example.com", score=100)

        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        trip_data = CreateTripRequest(
            email=user_data["email"],
            route=RouteIdentifierSchema(bus_line="8000", bus_direction=1),
            distance=0,
            data=datetime.now(UTC),
        )
        await client.post(
            "/trips/", json=trip_data.model_dump(mode="json"), headers=auth["headers"]
        )

        request_data = {"email": user_data["email"]}
        response = await client.post(
            "/rank/user",
            json=request_data,
            headers=auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 4

    @pytest.mark.asyncio
    async def test_get_user_rank_position_without_auth_fails(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        request_data = {"email": user_data["email"]}
        response = await client.post("/rank/user", json=request_data)

        assert response.status_code == 401


class TestGlobalRanking:
    @pytest.mark.asyncio
    async def test_get_global_ranking_should_work(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        await create_test_user_in_db(test_db, "first@example.com", score=1000)
        await create_test_user_in_db(test_db, "second@example.com", score=500)
        await create_test_user_in_db(test_db, "third@example.com", score=100)

        response = await client.get("/rank/global")

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert len(data["users"]) == 3

        scores = [user["score"] for user in data["users"]]
        assert scores == [1000, 500, 100]

        first_user = data["users"][0]
        assert "name" in first_user
        assert "email" in first_user
        assert "score" in first_user
        assert first_user["email"] == "first@example.com"

    @pytest.mark.asyncio
    async def test_get_global_ranking_returns_empty_when_no_users(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        response = await client.get("/rank/global")

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert len(data["users"]) == 0

    @pytest.mark.asyncio
    async def test_get_global_ranking_with_single_user(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
    ) -> None:
        await create_test_user_in_db(test_db, "solo@example.com", score=500)

        response = await client.get("/rank/global")

        assert response.status_code == 200
        data = response.json()

        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "solo@example.com"
        assert data["users"][0]["score"] == 500
