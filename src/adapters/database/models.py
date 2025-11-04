"""
SQLAlchemy ORM models.

These models map to database tables and are separate from domain models.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .connection import Base


class UserDB(Base):
    """
    User table model.

    Maps to the 'users' table in the database.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship to trips
    trips: Mapped[list["TripDB"]] = relationship(
        "TripDB", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserDB(email={self.email}, name={self.name}, score={self.score})>"


class TripDB(Base):
    """
    Trip table model.

    Maps to the 'trips' table in the database.
    """

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), ForeignKey("users.email"), nullable=False)
    bus_line: Mapped[str] = mapped_column(String(50), nullable=False)
    bus_direction: Mapped[int] = mapped_column(Integer, nullable=False)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationship to user
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="trips")

    def __repr__(self) -> str:
        return (
            f"<TripDB(id={self.id}, email={self.email}, "
            f"bus_line={self.bus_line}, score={self.score})>"
        )
