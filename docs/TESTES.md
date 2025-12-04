# 🧪 Guia de Testes - BusSP

## Executando os Testes

Execute a suite de testes com pytest:

```bash
# Execute todos os testes
pytest

# Execute com cobertura
pytest --cov=src --cov-report=html

# Execute arquivo de teste específico
pytest tests/core/test_trip_service_example.py

# Execute com saída detalhada
pytest -v
```

## Como Escrever Testes com Mocks

Este projeto utiliza **testes unitários isolados** com mocks para testar a lógica de negócio sem depender de banco de dados ou APIs externas.

### Por que usar Mocks?

Mocks permitem:
- **Isolar o código testado**: Testar apenas o serviço, sem depender de repositórios reais
- **Testes mais rápidos**: Sem I/O de banco de dados ou chamadas de rede
- **Controle total**: Simular diferentes cenários (sucesso, erro, casos extremos)
- **Testes determinísticos**: Resultados consistentes e previsíveis

### Exemplo Prático: Testando `TripService`

```python
import pytest
from unittest.mock import AsyncMock, create_autospec
from src.core.services.trip_service import TripService
from src.core.ports.user_repository import UserRepository
from src.core.ports.trip_repository import TripRepository
from src.core.models.user import User

@pytest.mark.asyncio
async def test_create_trip_calculates_score_correctly() -> None:
    """Testa cálculo de pontuação com mocks."""
    # 1. Arrange (Preparar) - Criar mocks
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)
    
    # Definir comportamento dos mocks
    test_user = User(
        name="Teste",
        email="test@example.com",
        score=0,
        password="hash"
    )
    user_repo.get_user_by_email = AsyncMock(return_value=test_user)
    user_repo.add_user_score = AsyncMock(return_value=test_user)
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)
    
    # Injetar mocks no serviço
    service = TripService(trip_repo, user_repo)
    
    # 2. Act (Agir) - Executar a função testada
    trip = await service.create_trip(
        email="test@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=1000,
        trip_datetime=datetime.now()
    )
    
    # 3. Assert (Verificar) - Checar resultados
    assert trip.score == 10  # 1000m = 10 pontos
    assert trip.email == "test@example.com"
    
    # Verificar que os métodos foram chamados corretamente
    user_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
    trip_repo.save_trip.assert_awaited_once()
    user_repo.add_user_score.assert_awaited_once_with("test@example.com", 10)
```

### Ferramentas Utilizadas

- **`create_autospec()`**: Cria um mock que respeita a interface original (detecta chamadas incorretas)
- **`AsyncMock`**: Mock para funções assíncronas (`async def`)
- **`return_value`**: Define o valor retornado pelo mock
- **`side_effect`**: Define comportamento customizado ou lança exceções
- **`assert_awaited_once_with()`**: Verifica que uma função async foi chamada uma vez com argumentos específicos

### Padrão AAA (Arrange-Act-Assert)

Organize seus testes em três seções:

1. **Arrange (Preparar)**: Configure mocks, dados de teste e estado inicial
2. **Act (Agir)**: Execute a função/método sendo testado
3. **Assert (Verificar)**: Confirme que o resultado está correto e mocks foram usados adequadamente

### Testando Casos de Erro

```python
@pytest.mark.asyncio
async def test_create_trip_fails_for_nonexistent_user() -> None:
    """Testa erro quando usuário não existe."""
    user_repo = create_autospec(UserRepository, instance=True)
    trip_repo = create_autospec(TripRepository, instance=True)
    
    # Mock retorna None (usuário não encontrado)
    user_repo.get_user_by_email = AsyncMock(return_value=None)
    
    service = TripService(trip_repo, user_repo)
    
    # Verifica que ValueError é lançado
    with pytest.raises(ValueError, match="not found"):
        await service.create_trip(
            email="ghost@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_datetime=datetime.now()
        )
    
    # Verifica que save_trip NÃO foi chamado
    trip_repo.save_trip.assert_not_awaited()
```

### Testando Múltiplas Chamadas

```python
@pytest.mark.asyncio
async def test_multiple_trips(mocker: "MockerFixture") -> None:
    """Testa múltiplas chamadas sequenciais ao serviço."""
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
    trip_repo.save_trip = AsyncMock(side_effect=lambda t: t)

    service = TripService(trip_repo, user_repo)

    # Act - Criar duas viagens
    trip1 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=500,
        trip_datetime=datetime.now(),
    )

    trip2 = await service.create_trip(
        email="bob@example.com",
        bus_line="8000",
        bus_direction=2,
        distance=1500,
        trip_datetime=datetime.now(),
    )

    # Assert
    assert trip1.score == 5
    assert trip2.score == 15
    assert trip_repo.save_trip.await_count == 2
    assert user_repo.add_user_score.await_count == 2
    user_repo.add_user_score.assert_any_await("bob@example.com", 5)
    user_repo.add_user_score.assert_any_await("bob@example.com", 15)
```

### Testando Erros de Infraestrutura

```python
@pytest.mark.asyncio
async def test_handles_repository_save_error(mocker: "MockerFixture") -> None:
    """Testa tratamento de erro quando repositório falha."""
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
    trip_repo.save_trip = AsyncMock(
        side_effect=RuntimeError("Database connection lost!")
    )

    service = TripService(trip_repo, user_repo)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Database connection lost"):
        await service.create_trip(
            email="charlie@example.com",
            bus_line="8000",
            bus_direction=1,
            distance=1000,
            trip_datetime=datetime.now(),
        )

    trip_repo.save_trip.assert_awaited_once()
    # Score não deve ser adicionado se o save falhar
    user_repo.add_user_score.assert_not_awaited()
```

## Boas Práticas em Testes

### ✅ FAÇA:

1. **Use `create_autospec()` para garantir type safety nos mocks**
   - Detecta chamadas incorretas em tempo de teste
   - Mantém compatibilidade com a interface

2. **Teste um comportamento por vez (testes focados)**
   ```python
   # Bom - testa apenas cálculo de score
   def test_calculates_score_correctly():
       ...
   
   # Bom - testa apenas validação de usuário
   def test_validates_user_exists():
       ...
   ```

3. **Nomeie testes descritivamente**
   - Padrão: `test_<o_que>_<quando>_<resultado_esperado>`
   - Exemplos:
     - `test_create_trip_calculates_score_correctly`
     - `test_create_trip_fails_for_nonexistent_user`
     - `test_handles_repository_save_error`

4. **Teste casos de sucesso E casos de erro**
   ```python
   # Teste o caminho feliz
   def test_create_user_success():
       ...
   
   # Teste validações
   def test_create_user_with_invalid_email_fails():
       ...
   
   # Teste erros de infraestrutura
   def test_create_user_handles_database_error():
       ...
   ```

5. **Verifique que mocks foram chamados corretamente**
   ```python
   user_repo.get_user_by_email.assert_awaited_once_with("test@example.com")
   trip_repo.save_trip.assert_not_awaited()
   ```

6. **Use pytest-mock para sintaxe mais limpa**
   ```python
   def test_something(mocker: "MockerFixture") -> None:
       mock = mocker.create_autospec(UserRepository, instance=True)
   ```

### ❌ NÃO FAÇA:

1. **Testar implementações internas**
   - Teste comportamento, não implementação
   - Se refatorar sem mudar comportamento, testes devem passar

2. **Criar testes que dependem de ordem de execução**
   ```python
   # Ruim - testes dependentes
   def test_step1():
       global user
       user = create_user()
   
   def test_step2():
       user.update()  # Depende de test_step1
   ```

3. **Ignorar casos extremos (edge cases)**
   - Teste valores nulos, vazios, negativos
   - Teste limites (0, -1, max_int)
   - Teste strings vazias, listas vazias

4. **Mockar tudo**
   - Mock apenas dependências externas (DB, APIs, I/O)
   - Não mock objetos de domínio simples
   ```python
   # Bom - mock apenas repositórios
   user_repo = create_autospec(UserRepository)
   test_user = User(name="Test")  # User real, não mock
   
   # Ruim - mockar tudo
   user_repo = create_autospec(UserRepository)
   test_user = create_autospec(User)  # Desnecessário
   ```

5. **Usar valores mágicos sem explicação**
   ```python
   # Ruim
   assert trip.score == 10
   
   # Bom - deixe claro de onde vem o valor
   distance = 1000
   expected_score = distance // 100
   assert trip.score == expected_score  # 10 pontos
   ```

## Estrutura de Testes

```
tests/
├── __init__.py
├── adapters/           # Testes de adaptadores (integração)
│   ├── test_user_repository_adapter.py
│   └── test_sptrans_adapter.py
├── core/              # Testes de lógica de negócio (unitários)
│   ├── test_trip_service.py
│   ├── test_user_service.py
│   └── test_score_service.py
└── web/               # Testes de controllers (integração)
    ├── test_trip_controller.py
    └── test_user_controller.py
```

## Cobertura de Testes

Mantenha cobertura alta na camada Core (lógica de negócio):

```bash
# Gerar relatório de cobertura
pytest --cov=src --cov-report=html

# Abrir relatório no navegador
open htmlcov/index.html
```

**Meta**: Mínimo 80% de cobertura na camada `src/core/`.

## Referências

- Exemplo completo: `tests/core/test_trip_service_example.py`
- Documentação pytest: https://docs.pytest.org/
- Documentação unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- pytest-mock: https://pytest-mock.readthedocs.io/
