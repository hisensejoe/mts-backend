from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.booking_request import BookingRequest, BookingRequestStatus
from app.models.trip import Trip, TripStatus
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.customer_portal import (
    CustomerAvailableVehicleRead,
    CustomerOverviewCounts,
    CustomerOverviewRead,
    CustomerShipmentDetailRead,
    CustomerShipmentRead,
)


def get_customer_overview(db: Session, customer_user: User) -> CustomerOverviewRead:
    customer_id = _require_customer_id(customer_user)

    total_shipments = _count_customer_trips(db, customer_id)
    active_shipments = _count_customer_trips(
        db,
        customer_id,
        statuses=(TripStatus.SCHEDULED, TripStatus.IN_PROGRESS),
    )
    completed_shipments = _count_customer_trips(
        db,
        customer_id,
        statuses=(TripStatus.COMPLETED,),
    )
    pending_booking_requests = _count_customer_booking_requests(
        db,
        customer_id,
        status_filter=BookingRequestStatus.PENDING,
    )
    total_shipment_value = (
        db.scalar(
            select(func.coalesce(func.sum(Trip.amount), 0)).where(
                Trip.customer_id == customer_id
            )
        )
        or Decimal("0")
    )

    recent_shipments = [
        _build_customer_shipment_read(trip)
        for trip in _get_recent_customer_trips(db, customer_id)
    ]

    return CustomerOverviewRead(
        counts=CustomerOverviewCounts(
            total_shipments=total_shipments,
            active_shipments=active_shipments,
            completed_shipments=completed_shipments,
            pending_booking_requests=pending_booking_requests,
        ),
        total_shipment_value=total_shipment_value,
        recent_shipments=recent_shipments,
    )


def list_customer_shipments(
    db: Session,
    customer_user: User,
    page: int,
    page_size: int,
) -> PaginatedResponse[CustomerShipmentRead]:
    customer_id = _require_customer_id(customer_user)
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = (
        select(Trip)
        .options(selectinload(Trip.milestones))
        .where(Trip.customer_id == customer_id)
    )
    count_statement = (
        select(func.count()).select_from(Trip).where(Trip.customer_id == customer_id)
    )

    total = db.scalar(count_statement) or 0
    trips = db.scalars(
        statement.order_by(Trip.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [_build_customer_shipment_read(trip) for trip in trips]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_customer_shipment_detail(
    db: Session,
    customer_user: User,
    trip_id: UUID,
) -> CustomerShipmentDetailRead:
    customer_id = _require_customer_id(customer_user)
    trip = db.scalar(
        select(Trip)
        .options(selectinload(Trip.milestones))
        .where(Trip.id == trip_id, Trip.customer_id == customer_id)
    )
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found.",
        )

    shipment = _build_customer_shipment_read(trip)
    return CustomerShipmentDetailRead(
        **shipment.model_dump(),
        route_id=trip.route_id,
        customer_id=trip.customer_id,
        waybill_number=trip.waybill_number,
        delivery_contact_name=trip.delivery_contact_name,
        delivery_contact_phone=trip.delivery_contact_phone,
        notes=trip.notes,
        cargo_description=trip.cargo_description,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


def list_available_vehicles_for_customer(
    db: Session,
    page: int,
    page_size: int,
) -> PaginatedResponse[CustomerAvailableVehicleRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Vehicle).where(Vehicle.status == VehicleStatus.AVAILABLE)
    count_statement = (
        select(func.count())
        .select_from(Vehicle)
        .where(Vehicle.status == VehicleStatus.AVAILABLE)
    )

    total = db.scalar(count_statement) or 0
    vehicles = db.scalars(
        statement.order_by(Vehicle.registration_number)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [
        CustomerAvailableVehicleRead(
            id=vehicle.id,
            registration_number=vehicle.registration_number,
            make=vehicle.make,
            model=vehicle.model,
            status=vehicle.status,
        )
        for vehicle in vehicles
    ]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def _require_customer_id(customer_user: User):
    if customer_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer user is not linked to a customer account.",
        )
    return customer_user.customer_id


def _count_customer_trips(
    db: Session,
    customer_id,
    statuses: tuple[TripStatus, ...] | None = None,
) -> int:
    statement = select(func.count()).select_from(Trip).where(Trip.customer_id == customer_id)
    if statuses is not None:
        statement = statement.where(Trip.status.in_(statuses))
    return db.scalar(statement) or 0


def _count_customer_booking_requests(
    db: Session,
    customer_id,
    status_filter: BookingRequestStatus | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(BookingRequest)
        .where(BookingRequest.customer_id == customer_id)
    )
    if status_filter is not None:
        statement = statement.where(BookingRequest.status == status_filter)
    return db.scalar(statement) or 0


def _get_recent_customer_trips(db: Session, customer_id) -> list[Trip]:
    return db.scalars(
        select(Trip)
        .options(selectinload(Trip.milestones))
        .where(Trip.customer_id == customer_id)
        .order_by(Trip.created_at.desc())
        .limit(5)
    ).all()


def _build_customer_shipment_read(trip: Trip) -> CustomerShipmentRead:
    latest_milestone = trip.milestones[-1] if trip.milestones else None
    return CustomerShipmentRead(
        id=trip.id,
        trip_reference=trip.trip_reference,
        status=trip.status,
        current_milestone=latest_milestone.status if latest_milestone else None,
        planned_pickup_at=trip.planned_pickup_at,
        delivery_address=trip.delivery_address,
        amount=trip.amount,
        assigned_vehicle_id=trip.assigned_vehicle_id,
        assigned_driver_id=trip.assigned_driver_id,
        booking_request_id=trip.booking_request_id,
    )
