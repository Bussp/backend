# BusSP - Sistema Gamificado de Rastreamento de Transporte Público

Sistema de rastreamento de ônibus com gamificação, desenvolvido em **Python** usando **FastAPI** e **Arquitetura Hexagonal**.

## Sobre o Projeto

Este projeto implementa um sistema gamificado onde usuários ganham pontos ao usar transporte público. A aplicação usa Arquitetura Hexagonal (Portas e Adaptadores) para manter a lógica de negócio isolada e testável.

**Tecnologias principais**:
- FastAPI (web framework)
- SQLAlchemy (ORM assíncrono)
- Pydantic V2 (validação)
- Pytest (testes)
- MyPy (tipagem estática)
- Ruff (linting e formatação)

## Quick Start

### Pré-requisitos

- Python 3.12 
- pip (gerenciador de pacotes Python)
- Git

### Instalação e Execução com Docker

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/Bussp/backend.git
   cd backend
   ```

2. **Construa a imagem Docker**:
   ```bash
   docker build -t backend .
   ```

3. **Execute o container**:
   ```bash
   docker run -d -p 127.0.0.1:8000:8000 backend
   ```

4. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação interativa (Swagger): http://localhost:8000/docs
   - Documentação alternativa (ReDoc): http://localhost:8000/redoc

5. **Para parar e remover o container**:
   
   Primeiro, pegue o ID do container:
   ```bash
   docker ps
   ```
   
   Você verá algo como:
   ```
   CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
   abc123def456   backend   ...       ...       ...       ...       ...
   ```
   
   Então execute:
   ```bash
   docker stop abc123def456
   docker rm abc123def456
   ```

### Instalação e Execução sem Docker

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/Bussp/backend.git
   cd backend
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python3.12 -m venv venv
   ```
   
   Ative o ambiente virtual:
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**:
   
   Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```
   
   Edite o arquivo `.env` e configure as seguintes variáveis:
   
   **Variáveis obrigatórias:**
   
   - `SPTRANS_API_TOKEN`: Token de acesso à API da SPTrans
     - **Como obter**: Acesse https://www.sptrans.com.br/desenvolvedores/
     - Faça cadastro e solicite um token de desenvolvedor
     - Substitua `your_api_token_here` pelo token recebido
     - Exemplo: `SPTRANS_API_TOKEN=abc123def456ghi789`
   
   **Variáveis opcionais (já vêm com valores padrão):**
   
   - `DATABASE_URL`: URL de conexão com o banco de dados
     - Padrão: `sqlite+aiosqlite:///./bussp.db` (SQLite local)
     - Para PostgreSQL (produção): `postgresql+asyncpg://usuario:senha@localhost:5432/bussp`
   
   - `DEBUG`: Modo de depuração
     - Padrão: `true`
     - Em produção, altere para `false`
   
   - `HOST` e `PORT`: Endereço e porta do servidor
     - Padrão: `0.0.0.0:8000`
     - Mantenha os valores padrão para desenvolvimento local
   
   - `AUTH_DISABLED`: Desabilitar autenticação (apenas para testes)
     - Padrão: `false`
     - Deixe como `false` em produção
   
   - `DEFAULT_USER_EMAIL` e `DEFAULT_USER_NAME`: Usuário padrão para testes
     - Usado apenas quando `AUTH_DISABLED=true`
     - Pode manter os valores padrão ou personalizar
   
   **Exemplo de arquivo `.env` configurado:**
   ```env
   DEBUG=true
   APP_NAME="BusSP - Gamified Public Transport Tracker"
   
   DATABASE_URL=sqlite+aiosqlite:///./bussp.db
   
   SPTRANS_API_TOKEN=seu_token_aqui_obtido_no_site_da_sptrans
   SPTRANS_BASE_URL=http://api.olhovivo.sptrans.com.br/v2.1
   
   HOST=0.0.0.0
   PORT=8000
   
   AUTH_DISABLED=false
   DEFAULT_USER_EMAIL="seu_email@exemplo.com"
   DEFAULT_USER_NAME="Seu Nome"
   ```

5. **Inicie o servidor**:
   ```bash
   python -m src.main
   ```
   
   Você verá algo como:
   ```
   INFO:     Started server process [12345]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

6. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação interativa (Swagger): http://localhost:8000/docs
   - Documentação alternativa (ReDoc): http://localhost:8000/redoc

7. **Para parar o servidor**:
   - Pressione `Ctrl + C` no terminal

> **Nota**: As tabelas do banco de dados são criadas automaticamente na inicialização.

## Desenvolvimento

### Testes
```bash
pytest                              # Executar todos os testes
pytest --cov=src --cov-report=term  # Com cobertura
```

### Verificação de Tipos
```bash
mypy src/  # Verificar tipos com MyPy
```

### Qualidade de Código
```bash
ruff check --fix src/ tests/  # Lint e correções automáticas
ruff format src/ tests/       # Formatação
```

## Documentação

### Estrutura do Projeto
```
src/
├── core/              # Lógica de negócio (models, services, ports)
├── web/               # Apresentação (controllers, schemas)
└── adapters/          # Infraestrutura (database, repositories, external)
```

Consulte o [**Guia de Arquitetura**](docs/ARQUITETURA.md) e [**Diagrama da Arquitetura**](docs/arquitetura.pdf) para detalhes completos sobre a estrutura e responsabilidades de cada camada.
