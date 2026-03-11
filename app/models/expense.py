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


class ExpenseType(str, Enum):
    FUEL = "fuel"
    PER_DIEM = "per_diem"
    MAINTENANCE = "maintenance"
    TOLL = "toll"


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    trip_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("trips.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    vehicle_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    driver_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    recorded_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    expense_type: Mapped[ExpenseType] = mapped_column(
        SqlEnum(
            ExpenseType,
            name="expense_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(String(255))
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trip: Mapped[Optional["Trip"]] = relationship(back_populates="expenses")
    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="expenses")
    driver: Mapped[Optional["Driver"]] = relationship(back_populates="expenses")
    recorded_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="expenses_recorded"
    )
