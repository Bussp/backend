# BusSP - Sistema Gamificado de Rastreamento de Transporte Público

## 🏗️ Arquitetura

Este projeto implementa **Arquitetura Hexagonal** (também conhecida como Portas e Adaptadores), um padrão de design que promove:

- **Separação de Responsabilidades**: Limites claros entre lógica de negócio, infraestrutura e apresentação
- **Testabilidade**: A lógica de negócio principal pode ser testada sem dependências externas
- **Flexibilidade**: Fácil trocar implementações (ex: mudar bancos de dados, adicionar novas APIs)
- **Manutenibilidade**: Mudanças em uma camada não afetam negativamente as outras

### As Três Camadas

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

### Regra de Dependência

**Dependências apontam para dentro**: `Web → Core ← Adapters`

- **Camada Web** depende da **Camada Core** (chama serviços)
- **Camada Adapters** depende da **Camada Core** (implementa portas)
- As camadas **Web** e **Adapters** nunca conhecem uma à outra
- **Camada Core** tem ZERO dependências externas

Isso garante que a lógica de negócio permaneça pura e independente de frameworks, bancos de dados e serviços externos.

## 📁 Estrutura do Projeto

### Responsabilidades das Camadas

#### 🎯 Camada Core (`src/core/`)

O **coração** da aplicação contendo lógica de negócio pura.

- **`models/`**: Entidades de domínio como dataclasses simples (User, Trip, Bus, Coordinate)
- **`ports/`**: Interfaces abstratas (ABC) definindo contratos para infraestrutura
  - `UserRepository`, `TripRepository`, `SpTransPort`, etc.
- **`services/`**: Orquestração da lógica de negócio
  - Exemplo: `TripService.create_trip()` calcula pontuações, valida usuários, salva viagens

**Princípio Chave**: Sem importações de frameworks web, bancos de dados ou bibliotecas externas. Apenas biblioteca padrão do Python e lógica de domínio.

#### 🌐 Camada Web (`src/web/`)

Trata requisições e respostas HTTP.

- **`controllers/`**: Routers do FastAPI com endpoints
  - Recebe requisições HTTP
  - Valida com schemas Pydantic
  - Chama serviços do core
  - Retorna respostas HTTP
- **`schemas.py`**: Modelos Pydantic V2 para requisições/respostas da API
- **`mappers.py`**: Funções para converter entre schemas da API e modelos de domínio

**Princípio Chave**: Controllers são finos. Eles delegam toda lógica de negócio aos serviços do core.

#### 🔌 Camada Adapters (`src/adapters/`)

Implementa aspectos de infraestrutura.

- **`database/`**:
  - `connection.py`: Configuração assíncrona do SQLAlchemy
  - `models.py`: Modelos ORM (UserDB, TripDB)
  - `mappers.py`: Tradução Modelo BD ↔ Modelo de Domínio
- **`repositories/`**: Implementações concretas das portas de repositório
  - `UserRepositoryAdapter`, `TripRepositoryAdapter`, etc.
- **`external/`**: Clientes de serviços externos
  - `SpTransAdapter`: Integração com API SPTrans

**Princípio Chave**: Adaptadores implementam interfaces de porta da camada core. Eles traduzem entre sistemas externos e modelos de domínio.

## 🚀 Começando

### Pré-requisitos

- Python 3.11+
- pip

### Instalação

1. **Clone o repositório**:
   ```bash
   cd /home/kim/code/estudos/bussp
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**:

   Copie o arquivo de exemplo de ambiente e adicione seu token da API SPTrans:
   ```bash
   cp .env.example .env
   ```
   
   Depois edite `.env` e substitua `your_api_token_here` pelo seu token real da API SPTrans.
   Obtenha seu token em: https://www.sptrans.com.br/desenvolvedores/

### Executando a Aplicação

1. **Inicie o servidor**:
   ```bash
   python -m src.main
   ```

2. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação interativa (gerada automaticamente pelo FastAPI): http://localhost:8000/docs
   - Documentação alternativa (gerada automaticamente pelo FastAPI): http://localhost:8000/redoc

### Inicialização do Banco de Dados

As tabelas do banco de dados são criadas automaticamente na inicialização da aplicação. Para controle manual:

```python
# No shell Python ou script
from src.adapters.database.connection import create_tables, drop_tables
import asyncio

# Criar tabelas
asyncio.run(create_tables())

# Remover tabelas (cuidado!)
asyncio.run(drop_tables())
```

## 🧪 Testes

Execute a suite de testes com pytest:

```bash
# Execute todos os testes
pytest

# Execute com cobertura
pytest --cov=src --cov-report=html

# Execute arquivo de teste específico
pytest tests/core/test_user_service.py

# Execute com saída detalhada
pytest -v
```

## 🔍 Verificação de Tipos

Este projeto usa **verificação de tipos rigorosa** com mypy:

```bash
# Verifique todos os arquivos
mypy src/

# Verifique arquivo específico
mypy src/core/services/user_service.py
```

**Configuração**: Veja `mypy.ini` para regras de verificação de tipos rigorosa.

## 🎨 Qualidade de Código

### Formatação e Linting com Ruff

Ruff trata tanto linting quanto formatação (substituindo Black e outras ferramentas):

```bash
# Verifique problemas
ruff check src/ tests/

# Corrija problemas auto-corrigíveis
ruff check --fix src/ tests/

# Formate o código
ruff format src/ tests/

# Verifique e formate de uma vez
ruff check --fix src/ tests/ && ruff format src/ tests/
```

**Configuração**: Veja `pyproject.toml` para configurações do Ruff.

### Boas Práticas

✅ **FAÇA:**
- Mantenha modelos de domínio livres de código de framework
- Use injeção de dependência para todos os serviços
- Escreva testes para lógica de negócio isoladamente
- Use type hints em todo lugar
- Siga a regra de dependência

❌ **NÃO FAÇA:**
- Importar FastAPI/SQLAlchemy na camada core
- Colocar lógica de negócio em controllers
- Acessar bancos de dados diretamente dos serviços
- Pular verificação de tipos
