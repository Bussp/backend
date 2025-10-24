"""User history domain model."""

from dataclasses import dataclass

from .trip import Trip


@dataclass
class UserHistory:
    """
    User's trip history.

    Attributes:
        email: User's email
        trips: List of all trips made by the user
    """

    email: str
    trips: list[Trip]
