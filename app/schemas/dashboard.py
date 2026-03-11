from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.booking_request import BookingRequestStatus
from app.models.expense import ExpenseType
from app.models.trip import TripStatus


class DashboardCountSummary(BaseModel):
    pending_booking_requests: int
    active_trips: int
    available_vehicles: int
    available_drivers: int
    total_customers: int


class DashboardTripStatusSummary(BaseModel):
    status: TripStatus
    count: int


class DashboardBookingStatusSummary(BaseModel):
    status: BookingRequestStatus
    count: int


class DashboardExpenseTypeSummary(BaseModel):
    expense_type: ExpenseType
    total_amount: Decimal


class DashboardRecentTrip(BaseModel):
    trip_id: str
    trip_reference: str
    customer_id: str
    status: TripStatus
    planned_pickup_at: datetime
    current_milestone: Optional[str] = None
    amount: Decimal


class DashboardRecentBookingRequest(BaseModel):
    booking_request_id: str
    customer_id: str
    status: BookingRequestStatus
    pickup_location: str
    destination: str
    preferred_pickup_date: date
    quoted_amount: Decimal


class DashboardSummaryRead(BaseModel):
    counts: DashboardCountSummary
    trip_status_breakdown: list[DashboardTripStatusSummary]
    booking_status_breakdown: list[DashboardBookingStatusSummary]
    expense_totals_by_type: list[DashboardExpenseTypeSummary]
    recent_trips: list[DashboardRecentTrip]
    recent_booking_requests: list[DashboardRecentBookingRequest]
