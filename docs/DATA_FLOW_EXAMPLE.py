"""
Complete Data Flow Example - BusSP Application

This file demonstrates how a request flows through all three layers
of the Hexagonal Architecture, showing the transformation of data
at each stage.
"""

# ============================================================================
# SCENARIO: User logs a bus trip and earns points
# ============================================================================

"""
Step 1: HTTP Request (External World)
--------------------------------------
POST /trips/
Content-Type: application/json

{
    "email": "john@example.com",
    "busLine": "8000",
    "busDirection": 1,
    "distance": 5000,
    "data": "2024-10-16T14:30:00"
}
"""

# ============================================================================
# LAYER 1: WEB LAYER (src/web/)
# ============================================================================

"""
File: src/web/controllers/trip_controller.py
--------------------------------------------

@router.post("/", response_model=CreateTripResponse)
async def create_trip(
    request: CreateTripRequest,  # ← Pydantic validates this
    trip_service: TripService = Depends(),
):
"""

# Pydantic parses JSON into typed object:
request_schema = {
    "email": "john@example.com",
    "bus_line": "8000",  # Pydantic converts busLine → bus_line
    "bus_direction": 1,
    "distance": 5000,
    "data": "datetime(2024, 10, 16, 14, 30)",  # Pydantic parses string to datetime
}

# Controller extracts data and calls service:
"""
trip = await trip_service.create_trip(
    email=request.email,          # "john@example.com"
    bus_line=request.bus_line,    # "8000"
    bus_direction=request.bus_direction,  # 1
    distance=request.distance,    # 5000
    trip_date=request.data,       # datetime object
)
"""

# ============================================================================
# LAYER 2: CORE LAYER (src/core/)
# ============================================================================

"""
File: src/core/services/trip_service.py
---------------------------------------

class TripService:
    async def create_trip(
        self,
        email: str,
        bus_line: str,
        bus_direction: int,
        distance: int,
        trip_date: datetime,
    ) -> Trip:
"""

# Step 2.1: Verify user exists (uses port interface)
"""
user = await self.user_repository.get_user_by_email(email)
if not user:
    raise ValueError(f"User with email {email} not found")

# Port call → goes to adapter layer (see Layer 3)
"""

# Step 2.2: Apply business logic (score calculation)
"""
score = distance // 100  # 5000 // 100 = 50 points
"""

# Step 2.3: Create domain model
"""
trip = Trip(
    email="john@example.com",
    bus_line="8000",
    bus_direction=1,
    distance=5000,
    score=50,  # ← Business logic applied here!
    start_date=datetime(2024, 10, 16, 14, 30),
    end_date=datetime(2024, 10, 16, 14, 30),
)
"""

# Step 2.4: Save trip (uses port interface)
"""
saved_trip = await self.trip_repository.save_trip(trip)
"""

# Step 2.5: Update user score (uses port interface)
"""
await self.user_repository.add_user_score(email, score)
"""

# ============================================================================
# LAYER 3: ADAPTERS LAYER (src/adapters/)
# ============================================================================

"""
File: src/adapters/repositories/trip_repository_adapter.py
----------------------------------------------------------

class TripRepositoryAdapter(TripRepository):
    async def save_trip(self, trip: Trip) -> Trip:
"""

# Step 3.1: Convert domain model → database model
"""
# Using: src/adapters/database/mappers.py

def map_trip_domain_to_db(trip: Trip) -> TripDB:
    return TripDB(
        email=trip.email,
        bus_line=trip.bus_line,
        bus_direction=trip.bus_direction,
        distance=trip.distance,
        score=trip.score,
        start_date=trip.start_date,
        end_date=trip.end_date,
    )
"""

# Step 3.2: Save to database (SQLAlchemy ORM)
"""
trip_db = map_trip_domain_to_db(trip)
self.session.add(trip_db)  # ← SQLAlchemy magic
await self.session.flush()

# Database record:
# INSERT INTO trips (email, bus_line, bus_direction, distance, score, start_date, end_date)
# VALUES ('john@example.com', '8000', 1, 5000, 50, '2024-10-16 14:30:00', '2024-10-16 14:30:00')
"""

# Step 3.3: Convert database model → domain model (return)
"""
return map_trip_db_to_domain(trip_db)
"""

# ============================================================================
# RETURN PATH: Back up the layers
# ============================================================================

"""
Layer 3 (Adapter) returns → Layer 2 (Service)
    Trip(email='john@example.com', bus_line='8000', ..., score=50)

Layer 2 (Service) returns → Layer 1 (Controller)
    Trip(email='john@example.com', bus_line='8000', ..., score=50)

Layer 1 (Controller) maps to response schema:
    File: src/web/controllers/trip_controller.py
    
    return CreateTripResponse(score=trip.score)
    
    # Pydantic serializes to JSON:
    {
        "score": 50
    }
"""

# ============================================================================
# HTTP Response (External World)
# ============================================================================

"""
HTTP/1.1 201 Created
Content-Type: application/json

{
    "score": 50
}
"""

# ============================================================================
# DATA TRANSFORMATIONS SUMMARY
# ============================================================================

TRANSFORMATIONS = """
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW DIAGRAM                            │
└─────────────────────────────────────────────────────────────────────┘

1. HTTP JSON
   ↓ (FastAPI + Pydantic)
2. CreateTripRequest (Pydantic Schema)
   ↓ (Controller extracts data)
3. Primitive types (str, int, datetime)
   ↓ (Service receives)
4. Trip (Domain Model) ← Business logic applied here!
   ↓ (Mapper: domain → DB)
5. TripDB (SQLAlchemy ORM Model)
   ↓ (Database INSERT)
6. Database Record (SQL)
   ↓ (Database SELECT)
7. TripDB (SQLAlchemy ORM Model)
   ↓ (Mapper: DB → domain)
8. Trip (Domain Model)
   ↓ (Controller maps to response)
9. CreateTripResponse (Pydantic Schema)
   ↓ (FastAPI + Pydantic)
10. HTTP JSON


KEY INSIGHT: Each layer has its own representation of data!
- Web Layer:    Pydantic schemas (API contracts)
- Core Layer:   Domain models (business entities)
- Adapter Layer: ORM models (database tables)

Mappers translate between these representations, keeping layers decoupled.
"""

# ============================================================================
# ARCHITECTURE BENEFITS IN THIS EXAMPLE
# ============================================================================

BENEFITS = """
┌─────────────────────────────────────────────────────────────────────┐
│                    WHY THIS ARCHITECTURE ROCKS                      │
└─────────────────────────────────────────────────────────────────────┘

✅ TESTABILITY
   We can test TripService.create_trip() without:
   - Starting FastAPI server
   - Creating database tables
   - Making HTTP requests
   
   Just mock the repositories!

✅ FLEXIBILITY
   Want to change scoring algorithm? 
   → Only edit src/core/services/trip_service.py
   
   Want to switch from SQLite to PostgreSQL?
   → Only edit src/adapters/database/connection.py
   
   Want to add GraphQL API?
   → Add new web layer, reuse existing services

✅ MAINTAINABILITY
   Each layer has ONE responsibility:
   - Web: HTTP handling
   - Core: Business logic
   - Adapters: Infrastructure
   
   Changes are localized!

✅ TYPE SAFETY
   MyPy checks types at every layer:
   - Pydantic validates HTTP data
   - Type hints in services
   - SQLAlchemy typed mappings
"""

# ============================================================================
# TESTING THIS FLOW
# ============================================================================

TEST_EXAMPLE = """
# File: tests/core/test_trip_service.py

@pytest.mark.asyncio
async def test_create_trip_calculates_score():
    # Arrange: Mock repositories (NO database!)
    user_repo = MockUserRepository()
    trip_repo = MockTripRepository()
    
    # Add test user
    await user_repo.save_user(
        User(name="John", email="john@example.com", score=0)
    )
    
    # Create service with mocks
    service = TripService(trip_repo, user_repo)
    
    # Act: Call the service
    trip = await service.create_trip(
        email="john@example.com",
        bus_line="8000",
        bus_direction=1,
        distance=5000,
        trip_date=datetime(2024, 10, 16, 14, 30),
    )
    
    # Assert: Score calculated correctly
    assert trip.score == 50  # 5000 / 100
    
    # No FastAPI, no SQLAlchemy, just pure Python!
"""

if __name__ == "__main__":
    print(TRANSFORMATIONS)
    print(BENEFITS)
    print(TEST_EXAMPLE)
