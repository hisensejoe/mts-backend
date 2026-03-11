from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.booking_request import BookingRequestContainerType


class TripStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripMilestoneStatus(str, Enum):
    DEPART_BASE = "depart_base"
    ENTER_PORT = "enter_port"
    LOAD_CONTAINER = "load_container"
    GATE_OUT = "gate_out"
    IN_TRANSIT = "in_transit"
    ARRIVE_AT_CUSTOMER = "arrive_at_customer"
    START_OFFLOAD = "start_offload"
    FINISH_OFFLOAD = "finish_offload"
    START_RETURN = "start_return"
    DROP_CONTAINER = "drop_container"
    BACK_AT_BASE = "back_at_base"
    CANCELLED = "cancelled"


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    booking_request_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("booking_requests.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    trip_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    waybill_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        index=True,
    )
    route_id: Mapped[UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="RESTRICT"),
        index=True,
    )
    assigned_vehicle_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        index=True,
    )
    assigned_driver_id: Mapped[UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        index=True,
    )
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    container_type: Mapped[BookingRequestContainerType] = mapped_column(
        SqlEnum(
            BookingRequestContainerType,
            name="booking_request_container_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    cargo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    planned_pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    delivery_address: Mapped[str] = mapped_column(String(500))
    delivery_contact_name: Mapped[str] = mapped_column(String(255))
    delivery_contact_phone: Mapped[str] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TripStatus] = mapped_column(
        SqlEnum(
            TripStatus,
            name="trip_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TripStatus.SCHEDULED,
        server_default=TripStatus.SCHEDULED.value,
    )

    booking_request: Mapped[Optional["BookingRequest"]] = relationship(
        back_populates="trips"
    )
    customer: Mapped["Customer"] = relationship(back_populates="trips")
    route: Mapped["Route"] = relationship(back_populates="trips")
    assigned_vehicle: Mapped["Vehicle"] = relationship(back_populates="trips")
    assigned_driver: Mapped["Driver"] = relationship(back_populates="trips")
    created_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="trips_created"
    )
    expenses: Mapped[list["Expense"]] = relationship(back_populates="trip")
    milestones: Mapped[list["TripMilestone"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripMilestone.recorded_at",
    )


class TripMilestone(TimestampMixin, Base):
    __tablename__ = "trip_milestones"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    trip_id: Mapped[UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[TripMilestoneStatus] = mapped_column(
        SqlEnum(
            TripMilestoneStatus,
            name="trip_milestone_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    trip: Mapped["Trip"] = relationship(back_populates="milestones")
    recorded_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="trip_milestones_recorded"
    )
