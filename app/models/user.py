from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    pin_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        index=True,
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="users")
    booking_requests_requested: Mapped[list["BookingRequest"]] = relationship(
        back_populates="requested_by_user"
    )
    trips_created: Mapped[list["Trip"]] = relationship(back_populates="created_by_user")
    trip_milestones_recorded: Mapped[list["TripMilestone"]] = relationship(
        back_populates="recorded_by_user"
    )
    otp_challenges: Mapped[list["AuthOtpChallenge"]] = relationship(
        back_populates="user"
    )
