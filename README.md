# BusSP - Gamified Public Transport Tracking System

## 🏗️ Architecture

This project implements **Hexagonal Architecture** (also known as Ports and Adapters), a design pattern that promotes:

- **Separation of Concerns**: Clear boundaries between business logic, infrastructure, and presentation
- **Testability**: Core business logic can be tested without external dependencies
- **Flexibility**: Easy to swap implementations (e.g., change databases, add new APIs)
- **Maintainability**: Changes in one layer don't cascade to others

### The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        WEB LAYER                            │
│  (Controllers, Schemas, Mappers)                            │
│  - HTTP request handling                                    │
│  - API schema validation (Pydantic)                         │
│  - Request/Response mapping                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ depends on ↓
┌─────────────────────────────────────────────────────────────┐
│                        CORE LAYER                           │
│  (Models, Services, Ports)                                  │
│  - Business logic                                           │
│  - Domain models (entities)                                 │
│  - Port interfaces (contracts)                              │
│  - NO knowledge of databases, frameworks, or external APIs  │
└──────────────────────┬──────────────────────────────────────┘
                       ↑ implemented by
┌─────────────────────────────────────────────────────────────┐
│                      ADAPTERS LAYER                         │
│  (Repositories, Database, External Services)                │
│  - Port implementations                                     │
│  - Database operations (SQLAlchemy)                         │
│  - External API clients (SPTrans)                           │
│  - Infrastructure concerns                                  │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Rule

**Dependencies point inward**: `Web → Core ← Adapters`

- **Web Layer** depends on **Core Layer** (calls services)
- **Adapters Layer** depends on **Core Layer** (implements ports)
- **Web** and **Adapters** layers never know about each other
- **Core Layer** has ZERO external dependencies

This ensures the business logic remains pure and independent of frameworks, databases, and external services.

## 📁 Project Structure

```
.
├── src/
│   ├── core/                      # Business logic (heart of the app)
│   │   ├── models/                # Domain entities (5 files)
│   │   │   ├── user.py
│   │   │   ├── trip.py
│   │   │   ├── bus.py
│   │   │   ├── coordinate.py
│   │   │   └── user_history.py
│   │   ├── ports/                 # Interface contracts (4 files)
│   │   │   ├── user_repository.py
│   │   │   ├── trip_repository.py
│   │   │   ├── history_repository.py
│   │   │   └── sptrans_port.py
│   │   └── services/              # Business logic (5 files)
│   │       ├── user_service.py
│   │       ├── trip_service.py
│   │       ├── route_service.py
│   │       ├── score_service.py
│   │       └── history_service.py
│   │
│   ├── web/                       # HTTP presentation layer
│   │   ├── controllers/           # API endpoints (5 files)
│   │   │   ├── user_controller.py
│   │   │   ├── trip_controller.py
│   │   │   ├── route_controller.py
│   │   │   ├── rank_controller.py
│   │   │   └── history_controller.py
│   │   ├── schemas.py             # Pydantic API models
│   │   └── mappers.py             # Schema ↔ Domain conversion
│   │
│   ├── adapters/                  # Infrastructure implementations
│   │   ├── database/              # SQLAlchemy ORM & connection
│   │   │   ├── connection.py
│   │   │   ├── models.py
│   │   │   └── mappers.py
│   │   ├── repositories/          # Repository implementations (3 files)
│   │   │   ├── user_repository_adapter.py
│   │   │   ├── trip_repository_adapter.py
│   │   │   └── history_repository_adapter.py
│   │   └── external/              # External API clients
│   │       └── sptrans_adapter.py
│   │
│   ├── config.py                  # Application configuration
│   └── main.py                    # FastAPI app & DI wiring
│
├── tests/                         # Test suite
│   ├── core/
│   │   └── test_trip_service_example.py
│   ├── web/
│   └── adapters/
│
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
├── mypy.ini                       # Type checking configuration
├── .gitignore                     # Git ignore rules
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

### Layer Responsibilities

#### 🎯 Core Layer (`src/core/`)

The **heart** of the application containing pure business logic.

- **`models/`**: Domain entities as simple dataclasses (User, Trip, Bus, Coordinate)
- **`ports/`**: Abstract interfaces (ABC) defining contracts for infrastructure
  - `UserRepository`, `TripRepository`, `SpTransPort`, etc.
- **`services/`**: Business logic orchestration
  - Example: `TripService.create_trip()` calculates scores, validates users, saves trips

**Key Principle**: No imports from web frameworks, databases, or external libraries. Only Python standard library and domain logic.

#### 🌐 Web Layer (`src/web/`)

Handles HTTP requests and responses.

- **`controllers/`**: FastAPI routers with endpoints
  - Receive HTTP requests
  - Validate with Pydantic schemas
  - Call core services
  - Return HTTP responses
- **`schemas.py`**: Pydantic V2 models for API requests/responses
- **`mappers.py`**: Functions to convert between API schemas and domain models

**Key Principle**: Controllers are thin. They delegate all business logic to core services.

#### 🔌 Adapters Layer (`src/adapters/`)

Implements infrastructure concerns.

- **`database/`**:
  - `connection.py`: Async SQLAlchemy setup
  - `models.py`: ORM models (UserDB, TripDB)
  - `mappers.py`: DB model ↔ Domain model translation
- **`repositories/`**: Concrete implementations of repository ports
  - `UserRepositoryAdapter`, `TripRepositoryAdapter`, etc.
- **`external/`**: External service clients
  - `SpTransAdapter`: SPTrans API integration

**Key Principle**: Adapters implement port interfaces from the core layer. They translate between external systems and domain models.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

1. **Clone the repository**:
   ```bash
   cd /home/kim/code/estudos/bussp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   Copy the example environment file and add your SPTrans API token:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and replace `your_api_token_here` with your actual SPTrans API token.
   Get your token from: https://www.sptrans.com.br/desenvolvedores/

### Running the Application

1. **Start the server**:
   ```bash
   # Method 1: Using Python module (recommended)
   python -m src.main
   
   # Method 2: Using Uvicorn directly
   uvicorn src.main:app --reload
   ```

2. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Database Initialization

The database tables are automatically created on application startup. For manual control:

```python
# In Python shell or script
from src.adapters.database.connection import create_tables, drop_tables
import asyncio

# Create tables
asyncio.run(create_tables())

# Drop tables (caution!)
asyncio.run(drop_tables())
```

## 🧪 Testing

Run the test suite with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/core/test_user_service.py

# Run with verbose output
pytest -v
```

## 🔍 Type Checking

This project uses **strict type checking** with mypy:

```bash
# Check all files
mypy src/

# Check specific file
mypy src/core/services/user_service.py
```

**Configuration**: See `mypy.ini` for strict type checking rules.

## 🎨 Code Quality

### Formatting and Linting with Ruff

Ruff handles both linting and formatting (replacing Black and other tools):

```bash
# Check for issues
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Check and format in one go
ruff check --fix src/ tests/ && ruff format src/ tests/
```

**Configuration**: See `pyproject.toml` for Ruff settings.

## 📚 API Endpoints

### User Management

- `POST /users/register` - Create a new user account
- `POST /users/login` - Authenticate user
- `GET /users/{email}` - Get user details

### Trip Management

- `POST /trips/` - Log a new trip and earn points

### Routes & Bus Positions

- `POST /routes/positions` - Get real-time bus positions

### Ranking

- `POST /rank/user` - Get a user's rank position
- `GET /rank/global` - Get global leaderboard

### History

- `POST /history/` - Get user's trip history

## 🔧 Development

### Adding a New Feature

1. **Define domain model** in `src/core/models/` (if needed)
2. **Create/update port interface** in `src/core/ports/`
3. **Implement business logic** in `src/core/services/`
4. **Create API schema** in `src/web/schemas.py`
5. **Add controller endpoint** in `src/web/controllers/`
6. **Implement adapter** in `src/adapters/`
7. **Add mapper functions** in appropriate `mappers.py`
8. **Write tests** for each layer

#### Example: Adding Email Notifications

1. **Port**: Create `src/core/ports/email_port.py` with `EmailPort` interface
2. **Service**: Update services to use `EmailPort`
3. **Adapter**: Create `src/adapters/external/smtp_adapter.py` implementing `EmailPort`
4. **DI**: Wire it in `src/main.py`

No changes needed in core business logic!

### Best Practices

✅ **DO:**
- Keep domain models free of framework code
- Use dependency injection for all services
- Write tests for business logic in isolation
- Use type hints everywhere
- Follow the dependency rule

❌ **DON'T:**
- Import FastAPI/SQLAlchemy in core layer
- Put business logic in controllers
- Directly access databases from services
- Skip type checking

## 🏛️ Why Hexagonal Architecture?

### Traditional Layered Architecture Problems

```
Presentation → Business Logic → Data Access
```

- Tight coupling to databases and frameworks
- Hard to test without real database
- Difficult to change infrastructure
- Business logic gets polluted with technical details

### Hexagonal Architecture Solution

```
       Web
        ↓
    ← Core →
        ↑
    Adapters
```

**Benefits:**

1. **Testability**: Test business logic with mock adapters
2. **Flexibility**: Swap SQLAlchemy for MongoDB without touching core
3. **Focus**: Business logic stays pure and readable
4. **Scalability**: Add new adapters (GraphQL, gRPC) easily
5. **Maintainability**: Changes isolated to specific layers

## � Troubleshooting

### Import Errors
Run from project root, not from `src/`:
```bash
# ✅ Correct
python -m src.main

# ❌ Wrong
cd src && python main.py
```

### Database Issues
Delete the database and restart:
```bash
rm bussp.db
python -m src.main
```

### Type Checking Errors
Some errors from missing libraries are expected until you install dependencies. Install them and re-run mypy.

### SPTrans API Issues
- Verify your token is correct in `.env`
- Check if the API is accessible: `curl http://api.olhovivo.sptrans.com.br/v2.1`
- Token expires - you may need to request a new one

## �📖 Learning Resources

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) by Alistair Cockburn
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) by Robert C. Martin
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)

## 🎓 Key Takeaways

1. **Business logic is independent** - Core layer has zero framework dependencies
2. **Easy to test** - Mock repositories enable fast unit tests
3. **Flexible infrastructure** - Swap databases/APIs without touching business logic
4. **Type-safe** - Strict mypy checking catches errors early
5. **Production-ready** - Async/await, proper error handling, configuration management
