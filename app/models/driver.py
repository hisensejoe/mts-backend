from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlEnum, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DriverStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    INACTIVE = "inactive"


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    license_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    trip_count: Mapped[int] = mapped_column(default=0, server_default="0")
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    per_diem: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[DriverStatus] = mapped_column(
        SqlEnum(
            DriverStatus,
            name="driver_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=DriverStatus.AVAILABLE,
        server_default=DriverStatus.AVAILABLE.value,
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="assigned_driver")
    trips: Mapped[list["Trip"]] = relationship(back_populates="assigned_driver")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="driver")
