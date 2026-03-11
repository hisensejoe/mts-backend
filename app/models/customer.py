from uuid import UUID, uuid4

from typing import Optional

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    company_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    users: Mapped[list["User"]] = relationship(back_populates="customer")
    booking_requests: Mapped[list["BookingRequest"]] = relationship(
        back_populates="customer"
    )
    trips: Mapped[list["Trip"]] = relationship(back_populates="customer")
