"""
Pydantic V2 schemas for API requests and responses.

This module defines all the data transfer objects (DTOs) used by the API.
These are separate from domain models to maintain separation of concerns.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ===== Utils =====


class RouteIdentifierSchema(BaseModel):
    """Schema for route identifier."""

    bus_line: str = Field(..., description="Bus line")
    bus_direction: int = Field(
        1,  # default
        description="Direction (1 = ida, 2 = volta)",
        ge=1,
        le=2,
    )

    model_config = {"populate_by_name": True}


class CoordinateSchema(BaseModel):
    """Schema for geographic coordinates."""

    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")


class BusPositionSchema(BaseModel):
    """Schema for bus position information."""

    route: RouteIdentifierSchema
    position: CoordinateSchema
    time_updated: datetime = Field(..., description="Last update timestamp")

    model_config = {"populate_by_name": True}


class BusRouteSchema(BaseModel):
    """Schema for a resolved bus route (provider-specific ID + identifier)."""

    route_id: int = Field(..., description="Provider-specific route identifier")
    route: RouteIdentifierSchema


# ===== User Management Schemas =====


class UserCreateAccountRequest(BaseModel):
    """Request schema for creating a new user account."""

    name: str = Field(..., min_length=1, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")


class UserResponse(BaseModel):
    """Response schema for user information."""

    name: str
    email: str
    score: int

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response schema for login (JWT token)."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


# ===== Trip Management Schemas =====


class CreateTripRequest(BaseModel):
    route: RouteIdentifierSchema
    distance: int = Field(..., ge=0, description="Distance traveled in meters")
    data: datetime = Field(..., description="Trip date and time")

    model_config = {"populate_by_name": True}


class CreateTripResponse(BaseModel):
    """Response schema after creating a trip."""

    score: int = Field(..., description="Points earned from this trip")


# ===== Route Management Schemas =====


class BusPositionsRequest(BaseModel):
    """Request schema for querying bus positions."""

    routes: list[BusRouteSchema] = Field(
        ..., description="List of resolved routes (with route_id) to query positions"
    )


class BusPositionsResponse(BaseModel):
    """Response schema for bus positions."""

    buses: list[BusPositionSchema] = Field(..., description="List of bus positions")


class BusRoutesDetailsRequest(BaseModel):
    """Request schema for resolving route details."""

    routes: list[RouteIdentifierSchema] = Field(
        ..., description="List of routes (line + direction) to resolve"
    )


class BusRoutesDetailsResponse(BaseModel):
    """Response schema for route details."""

    routes: list[BusRouteSchema] = Field(
        ..., description="List of resolved routes with provider IDs"
    )


class RouteShapeResponse(BaseModel):
    """Response schema for route shape coordinates."""

    route_id: str = Field(..., description="Route identifier")
    shape_id: str = Field(..., description="GTFS shape identifier")
    points: list[CoordinateSchema] = Field(..., description="Ordered list of coordinates")


# ===== Ranking Schemas =====


class UserRankingResponse(BaseModel):
    position: int = Field(..., description="User's rank position")


class GlobalRankingResponse(BaseModel):
    """Response schema for global ranking."""

    users: list[UserResponse] = Field(..., description="List of users by rank")


# ===== History Schemas =====


class TripHistoryEntry(BaseModel):
    date: datetime = Field(..., description="Trip date and time")
    score: int = Field(..., description="Points earned from this trip")
    route: RouteIdentifierSchema = Field(..., description="Route identifier")


class HistoryResponse(BaseModel):
    """Response schema for user history."""

    trips: list[TripHistoryEntry] = Field(..., description="List of user trips")
