import pytest
from httpx import AsyncClient

from .conftest import create_user_and_login


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_create_account_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        response = await client.post("/users/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert data["score"] == 0
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_create_account_duplicate_email_fails(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        response1 = await client.post("/users/register", json=user_data)
        assert response1.status_code == 201

        response2 = await client.post("/users/register", json=user_data)
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_create_account_invalid_email_fails(
        self,
        client: AsyncClient,
    ) -> None:
        invalid_data = {
            "name": "Test User",
            "email": "not-an-email",
            "password": "securepassword123",
        }
        response = await client.post("/users/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_account_short_password_fails(
        self,
        client: AsyncClient,
    ) -> None:
        invalid_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "short",
        }
        response = await client.post("/users/register", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    @pytest.mark.asyncio
    async def test_login_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        # First, create the user
        await client.post("/users/register", json=user_data)

        # Then login
        response = await client.post(
            "/users/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        # Create user
        await client.post("/users/register", json=user_data)

        # Try login with wrong password
        response = await client.post(
            "/users/login",
            data={
                "username": user_data["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/users/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401


class TestGetUserInfo:
    @pytest.mark.asyncio
    async def test_get_user_info_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        auth = await create_user_and_login(client, user_data)

        response = await client.get("/users/me", headers=auth["headers"])

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert data["score"] == 0

    @pytest.mark.asyncio
    async def test_get_user_info_without_token_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/users/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_info_invalid_token_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401


class TestGetOtherUserInfo:
    @pytest.mark.asyncio
    async def test_get_other_user_info_should_work(
        self,
        client: AsyncClient,
    ) -> None:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123",
        }
        second_user_data = {
            "name": "Second User",
            "email": "second@example.com",
            "password": "anotherpassword123",
        }
        await client.post("/users/register", json=user_data)

        await client.post("/users/register", json=second_user_data)

        response = await client.get(f"/users/{user_data['email']}")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert data["score"] == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_info_fails(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/users/nonexistent@example.com")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
