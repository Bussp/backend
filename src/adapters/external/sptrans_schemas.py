"""
SPTrans API-specific schemas.

These DTOs are used exclusively for communication with the SPTrans API
and should not leak into the domain or web layers.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SPTransRouteResponse(BaseModel):
    """Schema for SPTrans route response."""

    cl: int = Field(..., description="Route code")
    lc: bool = Field(..., description="Is circular")
    lt: str = Field(..., description="Main direction")
    tl: int = Field(..., description="Type")
    sl: int = Field(..., description="Secondary type")
    tp: str = Field(..., description="Terminal principal")
    ts: str = Field(..., description="Terminal secundário")


class SPTransVehicleResponse(BaseModel):
    """Schema for SPTrans vehicle position response."""

    p: int = Field(..., description="Route code")
    a: bool = Field(..., description="Is accessible")
    ta: datetime = Field(..., description="Time updated")
    px: int = Field(..., description="Longitude * 10^6")
    py: int = Field(..., description="Latitude * 10^6")


class SPTransPositionsResponse(BaseModel):
    """Schema for SPTrans positions response."""

    hr: datetime = Field(..., alias="currentTime", description="Current time")
    vs: list[SPTransVehicleResponse] = Field(..., alias="vehicles", description="List of vehicles")

    model_config = {"populate_by_name": True}
