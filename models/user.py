from datetime import time
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model representing a Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Localization
    language_code: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False, comment="User's preferred language: en, ru, et"
    )

    # Timezone
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False, comment="User's timezone (e.g., 'Europe/Tallinn')"
    )

    # Onboarding status
    is_onboarded: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Whether user completed initial onboarding"
    )

    # Sleep goals (optional, set during onboarding)
    target_bedtime: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, comment="Target time to go to bed (e.g., 22:00)"
    )
    target_wake_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, comment="Target time to wake up (e.g., 06:00)"
    )
    target_sleep_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Target sleep duration in hours (e.g., 8)"
    )

    # Relationships
    sleep_sessions: Mapped[list["SleepSession"]] = relationship(
        "SleepSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username}, language={self.language_code})>"
