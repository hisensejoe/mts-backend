from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.booking_request import BookingRequestStatus
from app.models.trip import TripMilestoneStatus, TripStatus
from app.models.vehicle import VehicleStatus


class CustomerOverviewCounts(BaseModel):
    total_shipments: int
    active_shipments: int
    completed_shipments: int
    pending_booking_requests: int


class CustomerOverviewRead(BaseModel):
    counts: CustomerOverviewCounts
    total_shipment_value: Decimal
    recent_shipments: list["CustomerShipmentRead"]


class CustomerShipmentRead(BaseModel):
    id: UUID
    trip_reference: str
    status: TripStatus
    current_milestone: Optional[TripMilestoneStatus] = None
    planned_pickup_at: datetime
    delivery_address: str
    amount: Decimal
    assigned_vehicle_id: UUID
    assigned_driver_id: UUID
    booking_request_id: Optional[UUID] = None


class CustomerShipmentDetailRead(CustomerShipmentRead):
    route_id: UUID
    customer_id: UUID
    waybill_number: Optional[str] = None
    delivery_contact_name: str
    delivery_contact_phone: str
    notes: Optional[str] = None
    cargo_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CustomerAvailableVehicleRead(BaseModel):
    id: UUID
    registration_number: str
    make: str
    model: str
    status: VehicleStatus


class CustomerBookingRequestSummaryRead(BaseModel):
    id: UUID
    status: BookingRequestStatus
