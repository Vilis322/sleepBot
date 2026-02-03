from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class SleepSession(Base, TimestampMixin):
    """Sleep session model representing a single sleep tracking record."""

    __tablename__ = "sleep_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Sleep tracking times (stored in UTC)
    sleep_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="When user started sleeping (UTC)"
    )
    sleep_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When user woke up (UTC), NULL if still sleeping",
    )

    # Sleep duration in hours (calculated when sleep_end is set)
    duration_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Sleep duration in hours"
    )

    # Quality rating (1-10 scale, optional)
    quality_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Sleep quality rating (1.0 - 10.0)"
    )

    # Notes (optional text from user)
    note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User's notes about this sleep session"
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="sleep_sessions")

    def __repr__(self) -> str:
        status = "active" if self.sleep_end is None else "completed"
        return f"<SleepSession(id={self.id}, user_id={self.user_id}, status={status}, duration={self.duration_hours}h)>"

    @property
    def is_active(self) -> bool:
        """Check if the sleep session is currently active (not ended)."""
        return self.sleep_end is None

    def calculate_duration(self) -> Optional[float]:
        """Calculate sleep duration in hours.

        Returns:
            Duration in hours if sleep_end is set, None otherwise.
        """
        if self.sleep_end is None:
            return None
        delta = self.sleep_end - self.sleep_start
        return round(delta.total_seconds() / 3600, 2)
