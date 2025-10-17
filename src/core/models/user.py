"""User domain model."""

from dataclasses import dataclass


@dataclass
class User:
    """
    User entity representing a user in the gamified transport system.

    Attributes:
        name: The user's full name
        email: The user's email address (used as unique identifier)
        score: The user's accumulated points from trips (default: 0)
        password: The user's hashed password
    """

    name: str
    email: str
    score: int = 0
    password: str = ""
