"""
Architectural Diagram - BusSP Application

This file provides a visual representation of the Hexagonal Architecture.
"""

ARCHITECTURE_DIAGRAM = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           HEXAGONAL ARCHITECTURE                             ║
║                     BusSP - Gamified Transport Tracker                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                              🌐 WEB LAYER                                    │
│                        (External World Interface)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📱 HTTP Clients → FastAPI Controllers → 📄 Pydantic Schemas                │
│                           ↓                                                  │
│                     Web Mappers                                              │
│                           ↓                                                  │
│  Controllers:                                                                │
│    • user_controller.py    → POST /users/register, /users/login            │
│    • trip_controller.py    → POST /trips/                                   │
│    • route_controller.py   → POST /routes/positions                         │
│    • rank_controller.py    → GET /rank/global                               │
│    • history_controller.py → POST /history/                                 │
│                                                                              │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │ Depends on (calls services)
                                 ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                             🎯 CORE LAYER                                    │
│                    (Business Logic - Heart of the App)                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📦 DOMAIN MODELS (Pure Python Dataclasses)                                 │
│     • User (name, email, score, password)                                   │
│     • Trip (email, bus_line, distance, score, dates)                        │
│     • Bus (BusPosition, BusRoute, RouteIdentifier)                          │
│     • Coordinate (latitude, longitude)                                      │
│                                                                              │
│  🔧 SERVICES (Business Logic)                                               │
│     • UserService     → create_user(), login_user()                         │
│     • TripService     → create_trip() [calculates score]                    │
│     • RouteService    → get_bus_positions()                                 │
│     • ScoreService    → get_ranking()                                       │
│     • HistoryService  → get_user_history()                                  │
│                                                                              │
│  🔌 PORTS (Interfaces - Contracts)                                          │
│     • UserRepository (ABC)                                                   │
│     • TripRepository (ABC)                                                   │
│     • UserHistoryRepository (ABC)                                           │
│     • SpTransPort (ABC)                                                      │
│                                                                              │
│  ✨ KEY PRINCIPLE: NO external dependencies!                                │
│     No FastAPI, no SQLAlchemy, no HTTP - just pure Python                  │
│                                                                              │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 ↑ Implemented by
                                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                          🔌 ADAPTERS LAYER                                   │
│                     (Infrastructure Implementations)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  💾 DATABASE ADAPTERS                                                        │
│     • connection.py           → AsyncSession, create_tables()               │
│     • models.py (ORM)         → UserDB, TripDB (SQLAlchemy)                │
│     • database/mappers.py     → DB Models ↔ Domain Models                  │
│                                                                              │
│  🗄️ REPOSITORY IMPLEMENTATIONS (Implement Core Ports)                       │
│     • UserRepositoryAdapter   → implements UserRepository                   │
│     • TripRepositoryAdapter   → implements TripRepository                   │
│     • HistoryRepositoryAdapter → implements UserHistoryRepository           │
│                                                                              │
│  🌍 EXTERNAL SERVICE ADAPTERS                                                │
│     • SpTransAdapter          → implements SpTransPort                      │
│       - Calls SPTrans API                                                   │
│       - Translates API responses to Domain Models                           │
│                                                                              │
│  ✨ KEY PRINCIPLE: Depends on Core (implements ports)                       │
│     Never depends on Web layer                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                          DEPENDENCY INJECTION                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

main.py → Wires everything together:

    FastAPI App
        │
        ├─ Controllers (Web Layer)
        │     │
        │     └─ Depends(get_user_service)  ←─┐
        │                                      │
        ├─ Service Providers                  │
        │     │                               │
        │     ├─ get_user_service() ──────────┘
        │     │     │
        │     │     └─ Depends(get_user_repository)  ←─┐
        │     │                                         │
        └─ Repository Providers                        │
              │                                         │
              └─ get_user_repository() ────────────────┘
                    │
                    └─ Depends(get_db)  ← AsyncSession


╔══════════════════════════════════════════════════════════════════════════════╗
║                           REQUEST FLOW EXAMPLE                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

POST /trips/  (Create a trip and earn points)

1️⃣  HTTP Request arrives → trip_controller.py
    └─ Validates CreateTripRequest schema (Pydantic)

2️⃣  Controller calls → TripService.create_trip()
    └─ Service receives domain data (not HTTP data)

3️⃣  Service executes business logic:
    ├─ Verifies user exists (calls UserRepository)
    ├─ Calculates score
    └─ Saves trip (calls TripRepository)

4️⃣  Repository Adapter → TripRepositoryAdapter
    ├─ Maps domain Trip → TripDB (ORM model)
    ├─ Saves to database via SQLAlchemy
    └─ Maps TripDB → domain Trip

5️⃣  Service returns → domain Trip model

6️⃣  Controller receives trip:
    ├─ Maps domain Trip → CreateTripResponse schema
    └─ Returns HTTP 201 with {score: 10}


╔══════════════════════════════════════════════════════════════════════════════╗
║                             KEY BENEFITS                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ TESTABILITY
   • Test business logic without database/HTTP
   • Mock repositories in tests
   • Fast, isolated unit tests

✅ FLEXIBILITY
   • Swap SQLite → PostgreSQL: change 1 file (connection.py)
   • Replace SPTrans API: new adapter, same port

✅ MAINTAINABILITY
   • Changes isolated to specific layers
   • Clear boundaries and responsibilities
   • Easy to understand and navigate

✅ SCALABILITY
   • Add new features without touching existing code
   • Parallel development (teams work on different layers)
   • Core stays stable as infrastructure evolves


╔══════════════════════════════════════════════════════════════════════════════╗
║                            TESTING STRATEGY                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

🧪 UNIT TESTS (Core Layer)
   src/core/services/trip_service.py
        ↓ tested with
   tests/core/test_trip_service.py
        ↓ using
   Mock Repositories (no database!)

🧪 INTEGRATION TESTS (Web Layer)
   src/web/controllers/trip_controller.py
        ↓ tested with
   tests/web/test_trip_controller.py
        ↓ using
   FastAPI TestClient + Real Services

🧪 INTEGRATION TESTS (Adapters)
   src/adapters/repositories/trip_repository_adapter.py
        ↓ tested with
   tests/adapters/test_trip_repository.py
        ↓ using
   Test Database (SQLite in-memory)
"""

if __name__ == "__main__":
    print(ARCHITECTURE_DIAGRAM)
