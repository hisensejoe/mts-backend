from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.booking_request import BookingRequestContainerType
from app.models.trip import TripMilestoneStatus, TripStatus


class TripBase(BaseModel):
    booking_request_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    assigned_vehicle_id: UUID
    assigned_driver_id: UUID
    container_type: BookingRequestContainerType
    cargo_description: Optional[str] = Field(default=None, max_length=2000)
    amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    planned_pickup_at: datetime
    delivery_address: str = Field(min_length=1, max_length=500)
    delivery_contact_name: str = Field(min_length=1, max_length=255)
    delivery_contact_phone: str = Field(min_length=10, max_length=20)
    waybill_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class TripCreate(TripBase):
    trip_reference: Optional[str] = Field(default=None, min_length=3, max_length=50)


class TripUpdate(BaseModel):
    assigned_vehicle_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
    planned_pickup_at: Optional[datetime] = None
    delivery_address: Optional[str] = Field(default=None, min_length=1, max_length=500)
    delivery_contact_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    delivery_contact_phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
    )
    waybill_number: Optional[str] = Field(default=None, max_length=100)
    cargo_description: Optional[str] = Field(default=None, max_length=2000)
    amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    notes: Optional[str] = Field(default=None, max_length=2000)


class TripMilestoneCreate(BaseModel):
    status: TripMilestoneStatus
    recorded_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class TripMilestoneRead(BaseModel):
    id: UUID
    status: TripMilestoneStatus
    recorded_at: datetime
    notes: Optional[str] = None
    recorded_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class TripRead(BaseModel):
    id: UUID
    booking_request_id: Optional[UUID] = None
    trip_reference: str
    waybill_number: Optional[str] = None
    customer_id: UUID
    route_id: UUID
    assigned_vehicle_id: UUID
    assigned_driver_id: UUID
    created_by_user_id: Optional[UUID] = None
    container_type: BookingRequestContainerType
    cargo_description: Optional[str] = None
    amount: Decimal
    planned_pickup_at: datetime
    delivery_address: str
    delivery_contact_name: str
    delivery_contact_phone: str
    notes: Optional[str] = None
    status: TripStatus
    current_milestone: Optional[TripMilestoneStatus] = None
    latest_milestone_at: Optional[datetime] = None
    milestone_count: int = 0
    created_at: datetime
    updated_at: datetime


class TripDetailRead(TripRead):
    milestones: list[TripMilestoneRead] = Field(default_factory=list)


class TripListFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[TripStatus] = None
    customer_id: Optional[UUID] = None
    assigned_vehicle_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
