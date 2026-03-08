from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking_request import (
    BookingRequestContainerType,
    BookingRequestStatus,
)


class BookingRequestBase(BaseModel):
    pickup_location: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    container_type: BookingRequestContainerType
    weight_tonnes: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    preferred_pickup_date: date
    preferred_pickup_time: Optional[time] = None
    delivery_address: str = Field(min_length=1, max_length=500)
    recipient_name: str = Field(min_length=1, max_length=255)
    recipient_phone: str = Field(min_length=10, max_length=20)
    notes: Optional[str] = Field(default=None, max_length=2000)


class BookingRequestCreate(BookingRequestBase):
    pass


class BookingRequestAdminUpdate(BaseModel):
    status: BookingRequestStatus


class BookingRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    requested_by_user_id: Optional[UUID] = None
    route_id: UUID
    pickup_location: str
    destination: str
    container_type: BookingRequestContainerType
    weight_tonnes: Optional[Decimal] = None
    preferred_pickup_date: date
    preferred_pickup_time: Optional[time] = None
    delivery_address: str
    recipient_name: str
    recipient_phone: str
    notes: Optional[str] = None
    status: BookingRequestStatus
    quoted_amount: Decimal


class BookingRequestDetailRead(BookingRequestRead):
    created_at: datetime
    updated_at: datetime


class BookingRequestListFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[BookingRequestStatus] = None
    customer_id: Optional[UUID] = None
