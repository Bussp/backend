"""Coordinate domain model."""

from dataclasses import dataclass


@dataclass
class Coordinate:
    """
    Geographic coordinate representation.

    Attributes:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
    """

    latitude: float
    longitude: float
