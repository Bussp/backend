from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.user import User
from src.core.ports.password_hasher import PasswordHasherPort
from src.core.ports.user_repository import UserRepository
from src.core.services.user_service import UserService


@pytest.mark.asyncio
async def test_criar_usuario_com_sucesso() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    repositorio_usuario.get_user_by_email = AsyncMock(return_value=None)
    hasher_senha.hash = lambda senha: f"hash_{senha}"

    usuario_criado = User(
        name="Maria Silva",
        email="maria@email.com",
        password="hash_senha123",
        score=0,
    )
    repositorio_usuario.save_user = AsyncMock(return_value=usuario_criado)

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.create_user(
        name="Maria Silva",
        email="maria@email.com",
        password="senha123",
    )

    assert resultado.name == "Maria Silva"
    assert resultado.email == "maria@email.com"
    assert resultado.password == "hash_senha123"
    assert resultado.score == 0
    repositorio_usuario.get_user_by_email.assert_called_once_with("maria@email.com")
    repositorio_usuario.save_user.assert_called_once()


@pytest.mark.asyncio
async def test_criar_usuario_email_ja_existe() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    usuario_existente = User(
        name="João Souza",
        email="joao@email.com",
        password="hash_qualquer",
        score=15,
    )
    repositorio_usuario.get_user_by_email = AsyncMock(return_value=usuario_existente)

    servico = UserService(repositorio_usuario, hasher_senha)

    with pytest.raises(ValueError, match="User with email joao@email.com already exists"):
        await servico.create_user(
            name="João Santos",
            email="joao@email.com",
            password="outrasenha",
        )

    repositorio_usuario.get_user_by_email.assert_called_once_with("joao@email.com")
    repositorio_usuario.save_user.assert_not_called()


@pytest.mark.asyncio
async def test_buscar_usuario_encontrado() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    usuario_esperado = User(
        name="Ana Paula",
        email="ana@email.com",
        password="hash_senha",
        score=75,
    )
    repositorio_usuario.get_user_by_email = AsyncMock(return_value=usuario_esperado)

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.get_user("ana@email.com")

    assert resultado is not None
    assert resultado.name == "Ana Paula"
    assert resultado.email == "ana@email.com"
    assert resultado.score == 75
    repositorio_usuario.get_user_by_email.assert_called_once_with("ana@email.com")


@pytest.mark.asyncio
async def test_buscar_usuario_nao_encontrado() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    repositorio_usuario.get_user_by_email = AsyncMock(return_value=None)

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.get_user("inexistente@email.com")

    assert resultado is None
    repositorio_usuario.get_user_by_email.assert_called_once_with("inexistente@email.com")


@pytest.mark.asyncio
async def test_login_usuario_credenciais_validas() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    usuario_armazenado = User(
        name="Carlos Mendes",
        email="carlos@email.com",
        password="hash_minhasenha",
        score=120,
    )
    repositorio_usuario.get_user_by_email = AsyncMock(return_value=usuario_armazenado)
    hasher_senha.verify = lambda senha, hash: senha == "minhasenha" and hash == "hash_minhasenha"

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.login_user("carlos@email.com", "minhasenha")

    assert resultado is not None
    assert resultado.email == "carlos@email.com"
    assert resultado.name == "Carlos Mendes"
    repositorio_usuario.get_user_by_email.assert_called_once_with("carlos@email.com")


@pytest.mark.asyncio
async def test_login_usuario_senha_incorreta() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    usuario_armazenado = User(
        name="Roberto Lima",
        email="roberto@email.com",
        password="hash_senhareal",
        score=40,
    )
    repositorio_usuario.get_user_by_email = AsyncMock(return_value=usuario_armazenado)
    hasher_senha.verify = lambda senha, hash: senha == "senhareal" and hash == "hash_senhareal"

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.login_user("roberto@email.com", "senhaerrada")

    assert resultado is None
    repositorio_usuario.get_user_by_email.assert_called_once_with("roberto@email.com")


@pytest.mark.asyncio
async def test_login_usuario_nao_cadastrado() -> None:
    repositorio_usuario = create_autospec(UserRepository, instance=True)
    hasher_senha = create_autospec(PasswordHasherPort, instance=True)

    repositorio_usuario.get_user_by_email = AsyncMock(return_value=None)

    servico = UserService(repositorio_usuario, hasher_senha)

    resultado = await servico.login_user("naocadastrado@email.com", "qualquersenha")

    assert resultado is None
    repositorio_usuario.get_user_by_email.assert_called_once_with("naocadastrado@email.com")
