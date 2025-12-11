#  Arquitetura do BusSP

## Visão Geral

Este projeto implementa **Arquitetura Hexagonal** (também conhecida como Portas e Adaptadores), um padrão de design que promove:

- **Separação de Responsabilidades**: Limites claros entre lógica de negócio, infraestrutura e apresentação
- **Testabilidade**: A lógica de negócio principal pode ser testada sem dependências externas
- **Flexibilidade**: Fácil trocar implementações (ex: mudar bancos de dados, adicionar novas APIs)
- **Manutenibilidade**: Mudanças em uma camada não se propagam para outras

## As Três Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                        CAMADA WEB                           │
│  (Controllers, Schemas, Mappers)                            │
│  - Tratamento de requisições HTTP                           │
│  - Validação de schemas da API (Pydantic)                   │
│  - Mapeamento de Requisição/Resposta                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ depende de ↓
┌─────────────────────────────────────────────────────────────┐
│                        CAMADA CORE                          │
│  (Models, Services, Ports)                                  │
│  - Lógica de negócio                                        │
│  - Modelos de domínio (entidades)                           │
│  - Interfaces de portas (contratos)                         │
│  - SEM conhecimento de bancos de dados, frameworks ou APIs  │
└──────────────────────┬──────────────────────────────────────┘
                       ↑ implementada por
┌─────────────────────────────────────────────────────────────┐
│                      CAMADA ADAPTERS                        │
│  (Repositories, Database, External Services)                │
│  - Implementações de portas                                 │
│  - Operações de banco de dados (SQLAlchemy)                 │
│  - Clientes de API externa (SPTrans)                        │
│  - Aspectos de infraestrutura                               │
└─────────────────────────────────────────────────────────────┘
```

## Regra de Dependência

**Dependências apontam para dentro**: `Web → Core ← Adapters`

- **Camada Web** depende da **Camada Core** (chama serviços)
- **Camada Adapters** depende da **Camada Core** (implementa portas)
- As camadas **Web** e **Adapters** nunca conhecem uma à outra
- **Camada Core** tem ZERO dependências externas

Isso garante que a lógica de negócio permaneça pura e independente de frameworks, bancos de dados e serviços externos.

## Estrutura do Projeto

```
src/
├── core/              # Camada Core - Lógica de Negócio
│   ├── models/        # Entidades de domínio
│   ├── ports/         # Interfaces (contratos)
│   └── services/      # Lógica de negócio
│
├── web/               # Camada Web - Apresentação
│   ├── controllers/   # Endpoints da API
│   ├── schemas.py     # Modelos Pydantic
│   └── mappers.py     # Conversão API ↔ Domínio
│
└── adapters/          # Camada Adapters - Infraestrutura
    ├── database/      # Persistência
    ├── repositories/  # Implementação de portas
    └── external/      # APIs externas
```

## Responsabilidades das Camadas

###  Camada Core (`src/core/`)

O **coração** da aplicação contendo lógica de negócio pura.

#### `models/` - Entidades de Domínio
Entidades de negócio como dataclasses simples:
- `User`: Usuário do sistema
- `Trip`: Viagem de ônibus
- `Bus`: Informações do ônibus
- `Coordinate`: Coordenadas geográficas

**Características**:
- Apenas Python padrão (dataclasses)
- Sem dependências externas
- Representam conceitos do negócio
- Imutáveis ou com comportamento mínimo

**Exemplo**:
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    score: int
    password: str
```

#### `ports/` - Interfaces (Contratos)
Interfaces abstratas (ABC) definindo contratos para infraestrutura:
- `UserRepository`: Contrato para persistência de usuários
- `TripRepository`: Contrato para persistência de viagens
- `BusProviderPort`: Contrato para provedor de dados de ônibus

**Características**:
- Apenas interfaces (ABC)
- Define **O QUE** fazer, não **COMO**
- Permite múltiplas implementações
- Facilita testes com mocks

**Exemplo**:
```python
from abc import ABC, abstractmethod
from typing import Optional

class UserRepository(ABC):
    @abstractmethod
    async def get_user(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        ...
    
    @abstractmethod
    async def save_user(self, user: User) -> User:
        """Salva usuário no repositório."""
        ...
```

#### `services/` - Lógica de Negócio
Orquestração da lógica de negócio:
- `TripService`: Gerencia viagens (criar, calcular pontuação)
- `UserService`: Gerencia usuários (criar, atualizar, autenticar)
- `ScoreService`: Calcula pontuações
- `RouteService`: Processa rotas

**Características**:
- Contém regras de negócio
- Orquestra ports (não implementa)
- Usa injeção de dependência
- Totalmente testável

**Exemplo**:
```python
class TripService:
    def __init__(
        self,
        trip_repository: TripRepository,
        user_repository: UserRepository,
    ) -> None:
        self._trip_repo = trip_repository
        self._user_repo = user_repository
    
    async def create_trip(
        self,
        email: str,
        bus_line: str,
        distance: int,
        trip_datetime: datetime,
    ) -> Trip:
        
        user = await self._user_repo.get_user(email)
        if user is None:
            raise ValueError(f"User {email} not found")
        
        
        score = distance // 100
        
        
        trip = Trip(
            email=email,
            bus_line=bus_line,
            score=score,
            trip_datetime=trip_datetime,
        )
        
        
        saved_trip = await self._trip_repo.save_trip(trip)
        
        
        await self._user_repo.add_user_score(email, score)
        
        return saved_trip
```

**Princípio Chave**: Sem importações de frameworks web, bancos de dados ou bibliotecas externas. Apenas biblioteca padrão do Python e lógica de domínio.

###  Camada Web (`src/web/`)

Trata requisições e respostas HTTP.

#### `controllers/` - Endpoints da API
Routers do FastAPI que expõem a API:
- `user_controller.py`: Endpoints de usuário
- `trip_controller.py`: Endpoints de viagem
- `route_controller.py`: Endpoints de rota
- `rank_controller.py`: Endpoints de ranking

**Responsabilidades**:
- Receber requisições HTTP
- Validar entrada com Pydantic
- Chamar serviços do core
- Mapear respostas
- Retornar HTTP responses

**Exemplo**:
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("/", response_model=TripResponse)
async def create_trip(
    request: CreateTripRequest,
    trip_service: TripService = Depends(get_trip_service),
) -> TripResponse:
    
    trip = await trip_service.create_trip(
        email=request.email,
        bus_line=request.bus_line,
        distance=request.distance,
        trip_datetime=request.trip_datetime,
    )
    
    
    return TripResponse.from_domain(trip)
```

#### `schemas.py` - Modelos Pydantic
Modelos Pydantic V2 para validação de API:
- Request schemas (entrada)
- Response schemas (saída)

**Características**:
- Validação automática
- Serialização/deserialização
- Documentação automática (OpenAPI)
- Conversão de tipos

**Exemplo**:
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class CreateTripRequest(BaseModel):
    email: EmailStr
    bus_line: str
    distance: int
    trip_datetime: datetime

class TripResponse(BaseModel):
    id: int
    email: str
    bus_line: str
    score: int
    trip_datetime: datetime
```

#### `mappers.py` - Conversão de Dados
Funções para converter entre schemas da API e modelos de domínio:

**Exemplo**:
```python
def trip_response_from_domain(trip: Trip) -> TripResponse:
    return TripResponse(
        id=trip.id,
        email=trip.email,
        bus_line=trip.bus_line,
        score=trip.score,
        trip_datetime=trip.trip_datetime,
    )
```

**Princípio Chave**: Controllers são finos. Eles delegam toda lógica de negócio aos serviços do core.

### Camada Adapters (`src/adapters/`)

Implementa aspectos de infraestrutura.

#### `database/` - Persistência
Configuração e modelos de banco de dados:

- **`connection.py`**: Configuração assíncrona do SQLAlchemy
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine
  
  engine = create_async_engine("sqlite+aiosqlite:///bussp.db")
  ```

- **`models.py`**: Modelos ORM (UserDB, TripDB)
  ```python
  from sqlalchemy.orm import DeclarativeBase, Mapped
  
  class UserDB(Base):
      __tablename__ = "users"
      
      id: Mapped[int] = mapped_column(primary_key=True)
      name: Mapped[str]
      email: Mapped[str] = mapped_column(unique=True)
      score: Mapped[int]
  ```

- **`mappers.py`**: Tradução Modelo BD ↔ Modelo de Domínio
  ```python
  def user_from_db(user_db: UserDB) -> User:
      return User(
          name=user_db.name,
          email=user_db.email,
          score=user_db.score,
          password=user_db.password_hash,
      )
  ```

#### `repositories/` - Implementação de Portas
Implementações concretas das portas de repositório:
- `UserRepositoryAdapter`: Implementa `UserRepository`
- `TripRepositoryAdapter`: Implementa `TripRepository`
- `HistoryRepositoryAdapter`: Implementa `HistoryRepository`

**Características**:
- Implementam interfaces do core
- Lidam com persistência real
- Traduzem entre ORM e domínio
- Tratam erros de infraestrutura

**Exemplo**:
```python
class UserRepositoryAdapter(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def get_user(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserDB).where(UserDB.email == email)
        )
        user_db = result.scalar_one_or_none()
        
        if user_db is None:
            return None
        
        return user_from_db(user_db)
    
    async def save_user(self, user: User) -> User:
        user_db = user_to_db(user)
        self._session.add(user_db)
        await self._session.commit()
        await self._session.refresh(user_db)
        return user_from_db(user_db)
```

#### `external/` - APIs Externas
Clientes de serviços externos:
- `SpTransAdapter`: Integração com API SPTrans
- `sptrans_schemas.py`: Schemas da API SPTrans

**Características**:
- Implementam ports de serviços externos
- Encapsulam chamadas HTTP
- Tratam erros de rede
- Traduzem formatos externos

**Exemplo**:
```python
class SpTransAdapter(BusProviderPort):
    def __init__(self, api_token: str) -> None:
        self._token = api_token
        self._base_url = "http://api.olhovivo.sptrans.com.br/v2.1"
    
    async def get_bus_position(self, line: str) -> list[Bus]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/Posicao/Linha?codigoLinha={line}",
                headers={"Authorization": f"Bearer {self._token}"}
            )
            data = response.json()
            return [self._parse_bus(b) for b in data]
```

**Princípio Chave**: Adaptadores implementam interfaces de porta da camada core. Eles traduzem entre sistemas externos e modelos de domínio.

## Fluxo de Dados

### Exemplo: Criar uma Viagem

```
1. HTTP Request
   ↓
2. Controller (Web)
   - Valida request (Pydantic)
   - Chama TripService
   ↓
3. TripService (Core)
   - Valida regras de negócio
   - Calcula pontuação
   - Usa TripRepository (port)
   - Usa UserRepository (port)
   ↓
4. TripRepositoryAdapter (Adapter)
   - Converte Trip → TripDB
   - Salva no banco SQLAlchemy
   - Converte TripDB → Trip
   ↓
5. TripService (Core)
   - Retorna Trip
   ↓
6. Controller (Web)
   - Converte Trip → TripResponse
   - Retorna HTTP Response
```

## Benefícios da Arquitetura

### 1. Testabilidade
```python
# Testar lógica de negócio sem banco de dados
def test_trip_service():
    # Mock dos repositories
    trip_repo = create_autospec(TripRepository)
    user_repo = create_autospec(UserRepository)
    
    # Serviço usa mocks, não banco real
    service = TripService(trip_repo, user_repo)
    
    # Teste puro de lógica
    trip = await service.create_trip(...)
    assert trip.score == expected_score
```

### 2. Flexibilidade
```python
# Fácil trocar implementações
# SQLite → PostgreSQL
user_repo = PostgresUserRepository(session)

# API Real → Mock
bus_provider = MockBusProvider()

# Serviço não muda!
trip_service = TripService(trip_repo, user_repo)
```

### 3. Manutenibilidade
- Mudanças no banco de dados → apenas adapters
- Mudanças na API → apenas web layer
- Mudanças nas regras de negócio → apenas core
- Camadas isoladas = menos bugs

### 4. Evolução Gradual
```python
# Adicionar novo provider sem mudar core
class RedisUserRepository(UserRepository):
    # Nova implementação
    ...

# Trocar em um único lugar (dependency injection)
def get_user_repo():
    return RedisUserRepository()  # Era SQLAlchemyUserRepository
```