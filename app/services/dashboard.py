from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.booking_request import BookingRequest, BookingRequestStatus
from app.models.customer import Customer
from app.models.driver import Driver, DriverStatus
from app.models.expense import Expense, ExpenseType
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.dashboard import (
    DashboardBookingStatusSummary,
    DashboardCountSummary,
    DashboardExpenseTypeSummary,
    DashboardRecentBookingRequest,
    DashboardRecentTrip,
    DashboardSummaryRead,
    DashboardTripStatusSummary,
)


def get_dashboard_summary(db: Session) -> DashboardSummaryRead:
    counts = DashboardCountSummary(
        pending_booking_requests=_count_booking_requests(
            db, BookingRequestStatus.PENDING
        ),
        active_trips=_count_active_trips(db),
        available_vehicles=_count_vehicles(db, VehicleStatus.AVAILABLE),
        available_drivers=_count_drivers(db, DriverStatus.AVAILABLE),
        total_customers=db.scalar(select(func.count()).select_from(Customer)) or 0,
    )

    trip_status_breakdown = [
        DashboardTripStatusSummary(status=status, count=count)
        for status, count in _group_trip_status_counts(db)
    ]
    booking_status_breakdown = [
        DashboardBookingStatusSummary(status=status, count=count)
        for status, count in _group_booking_status_counts(db)
    ]
    expense_totals_by_type = [
        DashboardExpenseTypeSummary(
            expense_type=expense_type, total_amount=total_amount
        )
        for expense_type, total_amount in _group_expense_totals(db)
    ]

    recent_trips = []
    for trip in _get_recent_trips(db):
        latest_milestone = trip.milestones[-1] if trip.milestones else None
        recent_trips.append(
            DashboardRecentTrip(
                trip_id=str(trip.id),
                trip_reference=trip.trip_reference,
                customer_id=str(trip.customer_id),
                status=trip.status,
                planned_pickup_at=trip.planned_pickup_at,
                current_milestone=(
                    latest_milestone.status.value if latest_milestone else None
                ),
                amount=trip.amount,
            )
        )

    recent_booking_requests = [
        DashboardRecentBookingRequest(
            booking_request_id=str(booking_request.id),
            customer_id=str(booking_request.customer_id),
            status=booking_request.status,
            pickup_location=booking_request.pickup_location,
            destination=booking_request.destination,
            preferred_pickup_date=booking_request.preferred_pickup_date,
            quoted_amount=booking_request.quoted_amount,
        )
        for booking_request in _get_recent_booking_requests(db)
    ]

    return DashboardSummaryRead(
        counts=counts,
        trip_status_breakdown=trip_status_breakdown,
        booking_status_breakdown=booking_status_breakdown,
        expense_totals_by_type=expense_totals_by_type,
        recent_trips=recent_trips,
        recent_booking_requests=recent_booking_requests,
    )


def _count_booking_requests(db: Session, booking_status: BookingRequestStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(BookingRequest)
            .where(BookingRequest.status == booking_status)
        )
        or 0
    )


def _count_active_trips(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Trip)
            .where(Trip.status.in_((TripStatus.SCHEDULED, TripStatus.IN_PROGRESS)))
        )
        or 0
    )


def _count_vehicles(db: Session, vehicle_status: VehicleStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Vehicle)
            .where(Vehicle.status == vehicle_status)
        )
        or 0
    )


def _count_drivers(db: Session, driver_status: DriverStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Driver)
            .where(Driver.status == driver_status)
        )
        or 0
    )


def _group_trip_status_counts(db: Session) -> list[tuple[TripStatus, int]]:
    rows = db.execute(
        select(Trip.status, func.count()).group_by(Trip.status).order_by(Trip.status)
    ).all()
    return [(status, count) for status, count in rows]


def _group_booking_status_counts(db: Session) -> list[tuple[BookingRequestStatus, int]]:
    rows = db.execute(
        select(BookingRequest.status, func.count())
        .group_by(BookingRequest.status)
        .order_by(BookingRequest.status)
    ).all()
    return [(status, count) for status, count in rows]


def _group_expense_totals(db: Session) -> list[tuple[ExpenseType, Decimal]]:
    rows = db.execute(
        select(Expense.expense_type, func.coalesce(func.sum(Expense.amount), 0))
        .group_by(Expense.expense_type)
        .order_by(Expense.expense_type)
    ).all()
    return [(expense_type, total_amount) for expense_type, total_amount in rows]


def _get_recent_trips(db: Session) -> list[Trip]:
    return db.scalars(
        select(Trip)
        .options(selectinload(Trip.milestones))
        .order_by(Trip.created_at.desc())
        .limit(5)
    ).all()


def _get_recent_booking_requests(db: Session) -> list[BookingRequest]:
    return db.scalars(
        select(BookingRequest).order_by(BookingRequest.created_at.desc()).limit(5)
    ).all()
