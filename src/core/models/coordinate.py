"""Coordinate domain model."""

from pydantic import BaseModel


class Coordinate(BaseModel):
    """
    Geographic coordinate representation.

    Attributes:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
    """

    latitude: float
    longitude: float

    model_config = {"frozen": True}
