from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    manufacture_year: Mapped[int] = mapped_column(Integer)
    body_type: Mapped[str] = mapped_column(String(100))
    fuel_type: Mapped[str] = mapped_column(String(50))
    odometer_km: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[VehicleStatus] = mapped_column(
        SqlEnum(
            VehicleStatus,
            name="vehicle_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=VehicleStatus.AVAILABLE,
        server_default=VehicleStatus.AVAILABLE.value,
    )
    assigned_driver_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    assigned_driver: Mapped[Optional["Driver"]] = relationship(
        back_populates="vehicles"
    )
    trips: Mapped[list["Trip"]] = relationship(back_populates="assigned_vehicle")
