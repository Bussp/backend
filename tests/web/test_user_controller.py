from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.core.models.user import User
from src.main import app
from src.web.controllers.user_controller import get_user_service


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)


@pytest.fixture
def servico_usuario_mock() -> MagicMock:
    return MagicMock()


def test_criar_usuario_com_sucesso(cliente: TestClient, servico_usuario_mock: MagicMock) -> None:
    usuario_mock = User(
        name="Marcos Antônio",
        email="marcos@email.com",
        password="senha_hash",
        score=0,
    )
    servico_usuario_mock.create_user = AsyncMock(return_value=usuario_mock)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.post(
        "/users/register",
        json={
            "name": "Marcos Antônio",
            "email": "marcos@email.com",
            "password": "senhasegura123",
        },
    )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_201_CREATED
    dados = resposta.json()
    assert dados["name"] == "Marcos Antônio"
    assert dados["email"] == "marcos@email.com"
    assert dados["score"] == 0
    assert "password" not in dados


def test_criar_usuario_email_ja_cadastrado(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    servico_usuario_mock.create_user = AsyncMock(
        side_effect=ValueError("User with email marcos@email.com already exists")
    )

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.post(
        "/users/register",
        json={
            "name": "Marcos Silva",
            "email": "marcos@email.com",
            "password": "outrasenha",
        },
    )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in resposta.json()["detail"]


def test_login_usuario_sucesso(cliente: TestClient, servico_usuario_mock: MagicMock) -> None:
    usuario_mock = User(
        name="Beatriz Almeida",
        email="beatriz@email.com",
        password="senha_hash",
        score=150,
    )
    servico_usuario_mock.login_user = AsyncMock(return_value=usuario_mock)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.post(
        "/users/login",
        data={
            "username": "beatriz@email.com",
            "password": "minhasenha",
        },
    )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert "access_token" in dados
    assert dados["token_type"] == "bearer"
    assert isinstance(dados["access_token"], str)


def test_login_usuario_credenciais_invalidas(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    servico_usuario_mock.login_user = AsyncMock(return_value=None)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.post(
        "/users/login",
        data={
            "username": "beatriz@email.com",
            "password": "senhaerrada",
        },
    )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.json()["detail"] == "Invalid email or password"


def test_buscar_usuario_por_email_sucesso(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    usuario_mock = User(
        name="Rafael Gonçalves",
        email="rafael@email.com",
        password="senha_hash",
        score=70,
    )
    servico_usuario_mock.get_user = AsyncMock(return_value=usuario_mock)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.get("/users/rafael@email.com")

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert dados["name"] == "Rafael Gonçalves"
    assert dados["email"] == "rafael@email.com"
    assert dados["score"] == 70


def test_buscar_usuario_nao_encontrado(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    servico_usuario_mock.get_user = AsyncMock(return_value=None)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.get("/users/inexistente@email.com")

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert resposta.json()["detail"] == "User not found"


def test_buscar_informacoes_usuario_atual_com_token_valido(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    usuario_mock = User(
        name="Camila Rodrigues",
        email="camila@email.com",
        password="senha_hash",
        score=95,
    )
    servico_usuario_mock.get_user = AsyncMock(return_value=usuario_mock)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    with patch(
        "src.web.controllers.user_controller.verify_token", return_value={"sub": "camila@email.com"}
    ):
        resposta = cliente.get(
            "/users/me",
            headers={"Authorization": "Bearer token_valido_aqui"},
        )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert dados["name"] == "Camila Rodrigues"
    assert dados["email"] == "camila@email.com"
    assert dados["score"] == 95


def test_buscar_informacoes_usuario_atual_sem_token(cliente: TestClient) -> None:
    resposta = cliente.get("/users/me")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_buscar_informacoes_usuario_atual_token_invalido(
    cliente: TestClient, servico_usuario_mock: MagicMock
) -> None:
    servico_usuario_mock.get_user = AsyncMock(return_value=None)

    app.dependency_overrides[get_user_service] = lambda: servico_usuario_mock

    resposta = cliente.get(
        "/users/me",
        headers={"Authorization": "Bearer token_invalido"},
    )

    app.dependency_overrides.clear()

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_criar_usuario_dados_invalidos(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/users/register",
        json={
            "name": "Gabriel Fernandes",
        },
    )

    assert resposta.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_usuario_sem_senha(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/users/login",
        data={
            "username": "gabriel@email.com",
        },
    )

    assert resposta.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
