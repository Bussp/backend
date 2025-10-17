"""
Pydantic V2 schemas for API requests and responses.

This module defines all the data transfer objects (DTOs) used by the API.
These are separate from domain models to maintain separation of concerns.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field

# ===== Utils =====


class RouteIdentifierSchema(BaseModel):
    """Schema for route identifier."""

    bus_line: str = Field(..., alias="busLine", description="Bus line")
    bus_direction: int = Field(
        ..., alias="busDirection", ge=1, le=2, description="Direction"
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
    time_updated: datetime = Field(..., alias="timeUpdated")

    model_config = {"populate_by_name": True}


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


# ===== Trip Management Schemas =====


class CreateTripRequest(BaseModel):
    """Request schema for creating a new trip."""

    email: EmailStr = Field(..., description="User's email")
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

    routes: List[RouteIdentifierSchema] = Field(
        ..., description="List of routes to query"
    )


class BusPositionsResponse(BaseModel):
    """Response schema for bus positions."""

    buses: List[BusPositionSchema] = Field(..., description="List of bus positions")


# ===== Ranking Schemas =====


class UserRankingRequest(BaseModel):
    """Request schema for getting a user's ranking."""

    email: EmailStr = Field(..., description="User's email")


class UserRankingResponse(BaseModel):
    """Response schema for user ranking."""

    position: int = Field(..., description="User's rank position")


class GlobalRankingResponse(BaseModel):
    """Response schema for global ranking."""

    users: List[UserResponse] = Field(..., description="List of users by rank")


# ===== History Schemas =====


class HistoryRequest(BaseModel):
    """Request schema for getting user history."""

    email: EmailStr = Field(..., description="User's email")


class TripHistoryEntry(BaseModel):
    """Schema for a single trip history entry."""

    date: datetime = Field(..., description="Trip date and time")
    score: int = Field(..., description="Points earned from this trip")


class HistoryResponse(BaseModel):
    """Response schema for user history."""

    trips: List[TripHistoryEntry] = Field(..., description="List of user trips")
