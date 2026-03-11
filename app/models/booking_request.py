from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BookingRequestContainerType(str, Enum):
    CONTAINER_20FT = "20ft_container"
    CONTAINER_30FT = "30ft_container"
    CONTAINER_40FT = "40ft_container"
    DOUBLE_CONTAINER = "double_container"


class BookingRequestStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingRequest(TimestampMixin, Base):
    __tablename__ = "booking_requests"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        index=True,
    )
    requested_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    route_id: Mapped[UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="RESTRICT"),
        index=True,
    )
    pickup_location: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    container_type: Mapped[BookingRequestContainerType] = mapped_column(
        SqlEnum(
            BookingRequestContainerType,
            name="booking_request_container_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    weight_tonnes: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    preferred_pickup_date: Mapped[date] = mapped_column(Date)
    preferred_pickup_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    delivery_address: Mapped[str] = mapped_column(String(500))
    recipient_name: Mapped[str] = mapped_column(String(255))
    recipient_phone: Mapped[str] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[BookingRequestStatus] = mapped_column(
        SqlEnum(
            BookingRequestStatus,
            name="booking_request_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=BookingRequestStatus.PENDING,
        server_default=BookingRequestStatus.PENDING.value,
    )
    quoted_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    customer: Mapped["Customer"] = relationship(back_populates="booking_requests")
    requested_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="booking_requests_requested"
    )
    route: Mapped["Route"] = relationship(back_populates="booking_requests")
    trips: Mapped[list["Trip"]] = relationship(back_populates="booking_request")
