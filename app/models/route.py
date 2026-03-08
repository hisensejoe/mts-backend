from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlEnum, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RouteType(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class Route(TimestampMixin, Base):
    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    distance_km: Mapped[int] = mapped_column()
    route_type: Mapped[RouteType] = mapped_column(
        SqlEnum(
            RouteType,
            name="route_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=RouteType.DOMESTIC,
        server_default=RouteType.DOMESTIC.value,
    )
    price_20ft: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_30ft: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_40ft: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_double: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    booking_requests: Mapped[list["BookingRequest"]] = relationship(
        back_populates="route"
    )
