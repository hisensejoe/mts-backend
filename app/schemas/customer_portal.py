from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.booking_request import (
    BookingRequestContainerType,
    BookingRequestStatus,
)
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
    assigned_vehicle_registration: Optional[str] = None
    assigned_driver_name: Optional[str] = None
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


class CustomerBookingRequestCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pickup_location: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("pickupLocation", "pickup_location"),
        serialization_alias="pickupLocation",
    )
    destination: str
    container_type: BookingRequestContainerType = Field(
        validation_alias=AliasChoices("containerType", "container_type"),
        serialization_alias="containerType",
    )
    weight_tonnes: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        validation_alias=AliasChoices("weightTonnes", "weight_tonnes"),
        serialization_alias="weightTonnes",
    )
    preferred_pickup_date: date = Field(
        validation_alias=AliasChoices("preferredPickupDate", "preferred_pickup_date"),
        serialization_alias="preferredPickupDate",
    )
    preferred_pickup_time: Optional[time] = Field(
        default=None,
        validation_alias=AliasChoices("preferredPickupTime", "preferred_pickup_time"),
        serialization_alias="preferredPickupTime",
    )
    delivery_address: str = Field(
        min_length=1,
        max_length=500,
        validation_alias=AliasChoices("deliveryAddress", "delivery_address"),
        serialization_alias="deliveryAddress",
    )
    recipient_name: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("recipientName", "recipient_name"),
        serialization_alias="recipientName",
    )
    recipient_phone: str = Field(
        min_length=10,
        max_length=20,
        validation_alias=AliasChoices("recipientPhone", "recipient_phone"),
        serialization_alias="recipientPhone",
    )
    notes: Optional[str] = None


class CustomerBookingRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    customer_id: UUID = Field(serialization_alias="customerId")
    requested_by_user_id: Optional[UUID] = Field(
        default=None,
        serialization_alias="requestedByUserId",
    )
    route_id: UUID = Field(serialization_alias="routeId")
    pickup_location: str = Field(serialization_alias="pickupLocation")
    destination: str
    container_type: BookingRequestContainerType = Field(serialization_alias="containerType")
    weight_tonnes: Optional[Decimal] = Field(
        default=None,
        serialization_alias="weightTonnes",
    )
    preferred_pickup_date: date = Field(serialization_alias="preferredPickupDate")
    preferred_pickup_time: Optional[time] = Field(
        default=None,
        serialization_alias="preferredPickupTime",
    )
    delivery_address: str = Field(serialization_alias="deliveryAddress")
    recipient_name: str = Field(serialization_alias="recipientName")
    recipient_phone: str = Field(serialization_alias="recipientPhone")
    notes: Optional[str] = None
    status: BookingRequestStatus
    quoted_amount: Decimal = Field(serialization_alias="quotedAmount")


class CustomerBookingRequestDetailRead(CustomerBookingRequestRead):
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
