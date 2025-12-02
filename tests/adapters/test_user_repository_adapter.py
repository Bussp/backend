from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.database.models import Base
from src.adapters.repositories.user_repository_adapter import UserRepositoryAdapter
from src.core.models.user import User


@pytest.fixture
async def sessao_bd() -> AsyncGenerator[AsyncSession, None]:
    motor = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with motor.begin() as conexao:
        await conexao.run_sync(Base.metadata.create_all)

    fabrica_sessao = async_sessionmaker(
        motor, class_=AsyncSession, expire_on_commit=False
    )

    async with fabrica_sessao() as sessao:
        yield sessao
        await sessao.rollback()

    await motor.dispose()


@pytest.mark.asyncio
async def test_salvar_usuario_com_sucesso(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)
    usuario = User(
        name="Pedro Oliveira",
        email="pedro@email.com",
        password="senha_hash",
        score=0,
    )

    resultado = await repositorio.save_user(usuario)
    await sessao_bd.commit()

    assert resultado.name == "Pedro Oliveira"
    assert resultado.email == "pedro@email.com"
    assert resultado.password == "senha_hash"
    assert resultado.score == 0


@pytest.mark.asyncio
async def test_salvar_usuario_email_duplicado(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)
    primeiro_usuario = User(
        name="Lucas Pereira",
        email="lucas@email.com",
        password="senha_hash",
        score=0,
    )
    segundo_usuario = User(
        name="Lucas Souza",
        email="lucas@email.com",
        password="outra_senha",
        score=10,
    )

    await repositorio.save_user(primeiro_usuario)
    await sessao_bd.commit()

    with pytest.raises(ValueError, match="User with email lucas@email.com already exists"):
        await repositorio.save_user(segundo_usuario)


@pytest.mark.asyncio
async def test_buscar_usuario_por_email_encontrado(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)
    usuario = User(
        name="Fernanda Costa",
        email="fernanda@email.com",
        password="senha_hash",
        score=60,
    )
    await repositorio.save_user(usuario)
    await sessao_bd.commit()

    resultado = await repositorio.get_user_by_email("fernanda@email.com")

    assert resultado is not None
    assert resultado.name == "Fernanda Costa"
    assert resultado.email == "fernanda@email.com"
    assert resultado.score == 60


@pytest.mark.asyncio
async def test_buscar_usuario_por_email_nao_encontrado(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)

    resultado = await repositorio.get_user_by_email("naoexiste@email.com")

    assert resultado is None


@pytest.mark.asyncio
async def test_listar_usuarios_ordenados_por_pontuacao(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)

    usuarios = [
        User(name="Usuario1", email="user1@email.com", password="pass", score=25),
        User(name="Usuario2", email="user2@email.com", password="pass", score=150),
        User(name="Usuario3", email="user3@email.com", password="pass", score=80),
    ]

    for usuario in usuarios:
        await repositorio.save_user(usuario)
    await sessao_bd.commit()

    resultado = await repositorio.get_all_users_ordered_by_score()

    assert len(resultado) == 3
    assert resultado[0].email == "user2@email.com"
    assert resultado[0].score == 150
    assert resultado[1].email == "user3@email.com"
    assert resultado[1].score == 80
    assert resultado[2].email == "user1@email.com"
    assert resultado[2].score == 25


@pytest.mark.asyncio
async def test_listar_usuarios_sem_registros(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)

    resultado = await repositorio.get_all_users_ordered_by_score()

    assert resultado == []


@pytest.mark.asyncio
async def test_adicionar_pontos_usuario(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)
    usuario = User(
        name="Ricardo Santos",
        email="ricardo@email.com",
        password="senha_hash",
        score=20,
    )
    await repositorio.save_user(usuario)
    await sessao_bd.commit()

    resultado = await repositorio.add_user_score("ricardo@email.com", 35)
    await sessao_bd.commit()

    assert resultado.score == 55

    usuario_atualizado = await repositorio.get_user_by_email("ricardo@email.com")
    assert usuario_atualizado is not None
    assert usuario_atualizado.score == 55


@pytest.mark.asyncio
async def test_adicionar_pontos_usuario_inexistente(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)

    with pytest.raises(ValueError, match="User with email invalido@email.com not found"):
        await repositorio.add_user_score("invalido@email.com", 10)


@pytest.mark.asyncio
async def test_adicionar_pontos_multiplas_vezes(sessao_bd: AsyncSession) -> None:
    repositorio = UserRepositoryAdapter(sessao_bd)
    usuario = User(
        name="Juliana Martins",
        email="juliana@email.com",
        password="senha_hash",
        score=0,
    )
    await repositorio.save_user(usuario)
    await sessao_bd.commit()

    await repositorio.add_user_score("juliana@email.com", 15)
    await sessao_bd.commit()
    await repositorio.add_user_score("juliana@email.com", 30)
    await sessao_bd.commit()
    resultado = await repositorio.add_user_score("juliana@email.com", 20)
    await sessao_bd.commit()

    assert resultado.score == 65
