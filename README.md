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
- pip

### Instalação e Execução com docker
1. **Clone o repositório**:
   ```bash
   cd /home/kim/code/estudos/bussp
   ```

2. **Execute**:
   ```bash
   docker run -d -p 127.0.0.1:8000:8000 backend
   ```

3. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação interativa: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

4. **Para matar o container**:
   Pegue o id do container em `CONTAINER ID`
   ```bash
   docker ps
   ```
   ```bash
   CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
   ```
   Execute:
   ```bash
   docker stop ${id}
   docker rm ${id}
   ```

### Instalação e Execução

1. **Clone o repositório**:
   ```bash
   cd bussp
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python3.12 -m venv venv # comando antigo: python -m venv venv

   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**:
   ```bash
   cp .env.example .env
   # Edite .env e adicione seu token da API SPTrans
   # Obtenha em: https://www.sptrans.com.br/desenvolvedores/
   ```

5. **Inicie o servidor**:
   ```bash
   python -m src.main
   ```

6. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação interativa: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

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

### Guias Completos
- [**Arquitetura**](docs/ARQUITETURA.md) - Arquitetura Hexagonal, camadas, responsabilidades e princípios
- [**Testes**](docs/TESTES.md) - Como escrever testes com mocks, padrão AAA, boas práticas
- [**Tipagem Estática**](docs/TIPAGEM.md) - Type hints, MyPy, erros comuns e soluções
- [**Linting**](docs/LINTING.md) - Ruff, qualidade de código, formatação automática

### Estrutura do Projeto
```
src/
├── core/              # Lógica de negócio (models, services, ports)
├── web/               # Apresentação (controllers, schemas)
└── adapters/          # Infraestrutura (database, repositories, external)
```

Consulte o [**Guia de Arquitetura**](docs/ARQUITETURA.md) para detalhes completos sobre a estrutura e responsabilidades de cada camada.
