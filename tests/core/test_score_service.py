from unittest.mock import AsyncMock, create_autospec

import pytest

from src.core.models.user import User
from src.core.ports.user_repository import UserRepository
from src.core.services.score_service import ScoreService


@pytest.mark.asyncio
async def test_get_user_ranking():
    """
    Testa Recepção do Ranking do Usuário
    """

    # 1. Configuração
    user_repo = create_autospec(UserRepository, instance=True)

    # Definir comportamento dos mocks
    test_user_1 = User(
        name="Maria da Silva", email="maria.silva@usp.br", score=0, password="123ABC"
    )
    test_user_2 = User(
        name="João dos Santos", email="joao.santos@usp.br", score=100, password="ABC123"
    )

    user_repo.get_all_users_ordered_by_score = AsyncMock(return_value=[test_user_2, test_user_1])

    # Injeção de mocks no serviço
    service = ScoreService(user_repo)

    # 2. Execução
    ranking = await service.get_user_ranking("joao.santos@usp.br")

    # 3. Verificação
    assert ranking == 1

    # Verifica se o método do repositório foi chamado corretamente
    user_repo.get_all_users_ordered_by_score.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_global_ranking():
    """
    Testa Recepção do Ranking Global
    """

    # 1. Configuração
    user_repo = create_autospec(UserRepository, instance=True)

    # Definir comportamento dos mocks
    test_user_1 = User(
        name="Maria da Silva", email="maria.silva@usp.br", score=0, password="123ABC"
    )
    test_user_2 = User(
        name="João dos Santos", email="joao.santos@usp.br", score=500, password="ABC123"
    )
    test_user_3 = User(
        name="Luana Rodrigues", email="luana.rodrigues@usp.br", score=100, password="ABC123"
    )

    user_repo.get_all_users_ordered_by_score = AsyncMock(
        return_value=[test_user_2, test_user_3, test_user_1]
    )

    # Injeção de mocks no serviço
    service = ScoreService(user_repo)

    # 2. Execução
    ranking = await service.get_global_ranking()

    # 3. Verificação
    assert ranking == [test_user_2, test_user_3, test_user_1]

    # Verifica se o método do repositório foi chamado corretamente
    user_repo.get_all_users_ordered_by_score.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_ranking_user_not_found():
    """
    Testa Recepção do Ranking do Usuário Não Encontrado
    """

    # 1. Configuração
    user_repo = create_autospec(UserRepository, instance=True)

    # Definir comportamento dos mocks
    test_user_1 = User(
        name="Maria da Silva", email="maria.silva@usp.br", score=0, password="123ABC"
    )

    user_repo.get_all_users_ordered_by_score = AsyncMock(return_value=[test_user_1])

    # Injeção de mocks no serviço
    service = ScoreService(user_repo)

    # 2. Execução
    ranking = await service.get_user_ranking("non.existent@usp.br")

    # 3. Verificação
    assert ranking is None

    # Verifica se o método do repositório foi chamado corretamente
    user_repo.get_all_users_ordered_by_score.assert_awaited_once()
