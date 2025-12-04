"""SPTrans API-specific schemas.

These DTOs are used exclusively for communication with the SPTrans API
and should not leak into the domain or web layers.
"""

from datetime import datetime

from pydantic import BaseModel, Field, RootModel


class SPTransLineInfo(BaseModel):
    """Schema for SPTrans line information response."""

    route_id: int = Field(..., alias="cl", description="Route code (internal SPTrans code)")
    is_circular: bool = Field(..., alias="lc", description="Is circular route")
    line_number: str = Field(..., alias="lt", description="Line number (e.g., '8000')")
    direction: int = Field(..., alias="sl", description="Direction (1 = ida, 2 = volta)")
    line_sufix: int = Field(..., alias="tl", description="Line type (10 = urban, etc.)")
    primary_terminal: str = Field(..., alias="tp", description="Primary terminal")
    secondary_terminal: str = Field(..., alias="ts", description="Secondary terminal")

    model_config = {"populate_by_name": True}


class SPTransLineSearchResponse(RootModel[list[SPTransLineInfo]]):
    """Schema for SPTrans line search response item."""

    root: list[SPTransLineInfo] = Field(..., description="List of line info results")


class SPTransVehicle(BaseModel):
    """Schema for SPTrans vehicle position."""

    vehicle_prefix: str = Field(..., alias="p", description="Vehicle prefix")
    is_accessible: bool = Field(..., alias="a", description="Is accessible")
    time_updated: datetime = Field(..., alias="ta", description="Time updated")
    latitude: float = Field(..., alias="py", description="Latitude")
    longitude: float = Field(..., alias="px", description="Longitude")

    model_config = {"populate_by_name": True}


class SPTransPositionsResponse(BaseModel):
    """Schema for SPTrans positions API response."""

    response_time: str = Field(..., alias="hr", description="Response time")
    vehicles: list[SPTransVehicle] = Field(
        default_factory=list, alias="vs", description="List of vehicles"
    )

    model_config = {"populate_by_name": True}
