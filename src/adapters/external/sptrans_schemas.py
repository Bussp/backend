"""
SPTrans API-specific schemas.

These DTOs are used exclusively for communication with the SPTrans API
and should not leak into the domain or web layers.
"""

from datetime import datetime

from pydantic import BaseModel, Field

class SPTransLineInfo(BaseModel):
    """Schema for SPTrans line information response."""

    cl: int = Field(..., description="Route code (internal SPTrans code)")
    lc: bool = Field(..., description="Is circular route")
    lt: str = Field(..., description="Line number (e.g., '8000')")
    sl: int = Field(..., description="Direction (1 = ida, 2 = volta)")
    tl: int = Field(..., description="Line type (10 = urban, etc.)")
    tp: str = Field(..., description="Primary terminal")
    ts: str = Field(..., description="Secondary terminal")

class SPTransLineSearchResponse(BaseModel):
    """Schema for SPTrans line search response item."""
    results: list[SPTransLineInfo] = Field(..., description="List of line info results")

class SPTransVehicle(BaseModel):
    """Schema for SPTrans vehicle position."""

    p: str = Field(..., description="Vehicle prefix")
    a: bool = Field(..., description="Is accessible")
    ta: datetime = Field(..., description="Time updated")
    py: float = Field(..., description="Latitude")
    px: float = Field(..., description="Longitude")


class SPTransPositionsResponse(BaseModel):
    """Schema for SPTrans positions API response."""

    hr: str = Field(..., description="Response time")
    vs: list[SPTransVehicle] = Field(default_factory=list, description="List of vehicles")
