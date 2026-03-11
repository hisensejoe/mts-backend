from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.booking_request import (
    BookingRequest,
    BookingRequestContainerType,
    BookingRequestStatus,
)
from app.models.customer import Customer
from app.models.driver import Driver, DriverStatus
from app.models.route import Route
from app.models.trip import Trip, TripMilestone, TripMilestoneStatus, TripStatus
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.trip import (
    TripCreate,
    TripDetailRead,
    TripListFilters,
    TripMilestoneCreate,
    TripMilestoneRead,
    TripRead,
    TripUpdate,
)

ACTIVE_TRIP_STATUSES = (TripStatus.SCHEDULED, TripStatus.IN_PROGRESS)
ORDERED_TRIP_MILESTONES = [
    TripMilestoneStatus.DEPART_BASE,
    TripMilestoneStatus.ENTER_PORT,
    TripMilestoneStatus.LOAD_CONTAINER,
    TripMilestoneStatus.GATE_OUT,
    TripMilestoneStatus.IN_TRANSIT,
    TripMilestoneStatus.ARRIVE_AT_CUSTOMER,
    TripMilestoneStatus.START_OFFLOAD,
    TripMilestoneStatus.FINISH_OFFLOAD,
    TripMilestoneStatus.START_RETURN,
    TripMilestoneStatus.DROP_CONTAINER,
    TripMilestoneStatus.BACK_AT_BASE,
]


def list_trips(
    db: Session,
    page: int,
    page_size: int,
    filters: TripListFilters,
) -> PaginatedResponse[TripRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Trip).options(selectinload(Trip.milestones))
    count_statement = select(func.count()).select_from(Trip)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Trip.trip_reference.ilike(pattern),
            Trip.waybill_number.ilike(pattern),
            Trip.delivery_contact_name.ilike(pattern),
            Trip.delivery_contact_phone.ilike(pattern),
            Trip.delivery_address.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.status is not None:
        statement = statement.where(Trip.status == filters.status)
        count_statement = count_statement.where(Trip.status == filters.status)

    if filters.customer_id is not None:
        statement = statement.where(Trip.customer_id == filters.customer_id)
        count_statement = count_statement.where(Trip.customer_id == filters.customer_id)

    if filters.assigned_vehicle_id is not None:
        statement = statement.where(
            Trip.assigned_vehicle_id == filters.assigned_vehicle_id
        )
        count_statement = count_statement.where(
            Trip.assigned_vehicle_id == filters.assigned_vehicle_id
        )

    if filters.assigned_driver_id is not None:
        statement = statement.where(
            Trip.assigned_driver_id == filters.assigned_driver_id
        )
        count_statement = count_statement.where(
            Trip.assigned_driver_id == filters.assigned_driver_id
        )

    total = db.scalar(count_statement) or 0
    trips = db.scalars(
        statement.order_by(Trip.planned_pickup_at.desc(), Trip.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [_build_trip_read(trip) for trip in trips]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_trip(db: Session, trip_id: UUID) -> Trip:
    trip = db.scalar(
        select(Trip)
        .options(
            joinedload(Trip.booking_request),
            joinedload(Trip.customer),
            joinedload(Trip.route),
            joinedload(Trip.assigned_vehicle),
            joinedload(Trip.assigned_driver),
            selectinload(Trip.milestones),
        )
        .where(Trip.id == trip_id)
    )
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found.",
        )
    return trip


def get_trip_detail(db: Session, trip_id: UUID) -> TripDetailRead:
    trip = get_trip(db, trip_id)
    return _build_trip_detail_read(trip)


def create_trip(
    db: Session,
    current_user: User,
    payload: TripCreate,
) -> TripDetailRead:
    booking_request = _resolve_booking_request(db, payload.booking_request_id)
    customer_id, route_id = _resolve_trip_scope(payload, booking_request)
    customer = _get_customer(db, customer_id)
    route = _get_route(db, route_id)
    vehicle = _get_assignable_vehicle(db, payload.assigned_vehicle_id)
    driver = _get_assignable_driver(db, payload.assigned_driver_id)

    if booking_request is not None:
        _ensure_booking_request_not_already_linked(db, booking_request.id)
        _validate_booking_request_against_payload(booking_request, payload)
        booking_request.status = BookingRequestStatus.CONFIRMED

    amount = payload.amount
    if amount is None:
        amount = (
            booking_request.quoted_amount
            if booking_request is not None
            else _resolve_route_amount(route, payload.container_type)
        )

    trip_reference = _resolve_trip_reference(db, payload.trip_reference)

    trip = Trip(
        booking_request_id=booking_request.id if booking_request else None,
        trip_reference=trip_reference,
        waybill_number=_clean_optional_string(payload.waybill_number),
        customer_id=customer.id,
        route_id=route.id,
        assigned_vehicle_id=vehicle.id,
        assigned_driver_id=driver.id,
        created_by_user_id=current_user.id,
        container_type=payload.container_type,
        cargo_description=_clean_optional_string(payload.cargo_description),
        amount=amount,
        planned_pickup_at=payload.planned_pickup_at,
        delivery_address=payload.delivery_address.strip(),
        delivery_contact_name=payload.delivery_contact_name.strip(),
        delivery_contact_phone=payload.delivery_contact_phone,
        notes=_clean_optional_string(payload.notes),
        status=TripStatus.SCHEDULED,
    )
    db.add(trip)

    vehicle.status = VehicleStatus.ON_TRIP
    driver.status = DriverStatus.ON_TRIP

    db.commit()
    db.refresh(trip)
    return get_trip_detail(db, trip.id)


def update_trip(
    db: Session,
    trip_id: UUID,
    payload: TripUpdate,
) -> TripDetailRead:
    trip = get_trip(db, trip_id)
    _ensure_trip_is_mutable(trip)
    changes = payload.model_dump(exclude_unset=True)

    previous_vehicle_id = trip.assigned_vehicle_id
    previous_driver_id = trip.assigned_driver_id

    if (
        "assigned_vehicle_id" in changes
        and changes["assigned_vehicle_id"] is not None
        and changes["assigned_vehicle_id"] != trip.assigned_vehicle_id
    ):
        vehicle = _get_assignable_vehicle(
            db,
            changes["assigned_vehicle_id"],
            exclude_trip_id=trip.id,
        )
        trip.assigned_vehicle_id = vehicle.id

    if (
        "assigned_driver_id" in changes
        and changes["assigned_driver_id"] is not None
        and changes["assigned_driver_id"] != trip.assigned_driver_id
    ):
        driver = _get_assignable_driver(
            db,
            changes["assigned_driver_id"],
            exclude_trip_id=trip.id,
        )
        trip.assigned_driver_id = driver.id

    if "planned_pickup_at" in changes:
        trip.planned_pickup_at = changes["planned_pickup_at"]

    if "delivery_address" in changes and changes["delivery_address"] is not None:
        trip.delivery_address = changes["delivery_address"].strip()

    if (
        "delivery_contact_name" in changes
        and changes["delivery_contact_name"] is not None
    ):
        trip.delivery_contact_name = changes["delivery_contact_name"].strip()

    if (
        "delivery_contact_phone" in changes
        and changes["delivery_contact_phone"] is not None
    ):
        trip.delivery_contact_phone = changes["delivery_contact_phone"]

    if "waybill_number" in changes:
        trip.waybill_number = _clean_optional_string(changes["waybill_number"])

    if "cargo_description" in changes:
        trip.cargo_description = _clean_optional_string(changes["cargo_description"])

    if "amount" in changes and changes["amount"] is not None:
        trip.amount = changes["amount"]

    if "notes" in changes:
        trip.notes = _clean_optional_string(changes["notes"])

    db.add(trip)
    db.commit()

    _refresh_vehicle_status_for_trip_change(
        db=db,
        current_vehicle_id=trip.assigned_vehicle_id,
        previous_vehicle_id=previous_vehicle_id,
        trip=trip,
    )
    _refresh_driver_status_for_trip_change(
        db=db,
        current_driver_id=trip.assigned_driver_id,
        previous_driver_id=previous_driver_id,
        trip=trip,
    )

    db.commit()
    db.refresh(trip)
    return get_trip_detail(db, trip.id)


def add_trip_milestone(
    db: Session,
    trip_id: UUID,
    current_user: User,
    payload: TripMilestoneCreate,
) -> TripDetailRead:
    trip = get_trip(db, trip_id)
    latest_milestone = trip.milestones[-1] if trip.milestones else None
    _validate_milestone_transition(latest_milestone, payload)

    milestone = TripMilestone(
        trip_id=trip.id,
        status=payload.status,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        notes=_clean_optional_string(payload.notes),
        recorded_by_user_id=current_user.id,
    )
    db.add(milestone)

    if payload.status == TripMilestoneStatus.CANCELLED:
        trip.status = TripStatus.CANCELLED
    elif payload.status == TripMilestoneStatus.BACK_AT_BASE:
        trip.status = TripStatus.COMPLETED
        driver = db.get(Driver, trip.assigned_driver_id)
        if driver is not None:
            driver.trip_count += 1
            db.add(driver)
    else:
        trip.status = TripStatus.IN_PROGRESS

    db.add(trip)
    db.commit()

    _refresh_vehicle_status(db, trip.assigned_vehicle_id)
    _refresh_driver_status(db, trip.assigned_driver_id)

    db.commit()
    db.refresh(trip)
    return get_trip_detail(db, trip.id)


def _build_trip_read(trip: Trip) -> TripRead:
    latest_milestone = trip.milestones[-1] if trip.milestones else None
    return TripRead(
        id=trip.id,
        booking_request_id=trip.booking_request_id,
        trip_reference=trip.trip_reference,
        waybill_number=trip.waybill_number,
        customer_id=trip.customer_id,
        route_id=trip.route_id,
        assigned_vehicle_id=trip.assigned_vehicle_id,
        assigned_driver_id=trip.assigned_driver_id,
        created_by_user_id=trip.created_by_user_id,
        container_type=trip.container_type,
        cargo_description=trip.cargo_description,
        amount=trip.amount,
        planned_pickup_at=trip.planned_pickup_at,
        delivery_address=trip.delivery_address,
        delivery_contact_name=trip.delivery_contact_name,
        delivery_contact_phone=trip.delivery_contact_phone,
        notes=trip.notes,
        status=trip.status,
        current_milestone=latest_milestone.status if latest_milestone else None,
        latest_milestone_at=latest_milestone.recorded_at if latest_milestone else None,
        milestone_count=len(trip.milestones),
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


def _build_trip_detail_read(trip: Trip) -> TripDetailRead:
    trip_read = _build_trip_read(trip)
    return TripDetailRead(
        **trip_read.model_dump(),
        milestones=[
            TripMilestoneRead(
                id=milestone.id,
                status=milestone.status,
                recorded_at=milestone.recorded_at,
                notes=milestone.notes,
                recorded_by_user_id=milestone.recorded_by_user_id,
                created_at=milestone.created_at,
                updated_at=milestone.updated_at,
            )
            for milestone in trip.milestones
        ],
    )


def _resolve_booking_request(
    db: Session,
    booking_request_id: Optional[UUID],
) -> Optional[BookingRequest]:
    if booking_request_id is None:
        return None

    booking_request = db.get(BookingRequest, booking_request_id)
    if booking_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found.",
        )
    if booking_request.status == BookingRequestStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancelled booking requests cannot be converted to trips.",
        )
    return booking_request


def _resolve_trip_scope(
    payload: TripCreate,
    booking_request: Optional[BookingRequest],
) -> tuple[UUID, UUID]:
    customer_id = (
        booking_request.customer_id if booking_request else payload.customer_id
    )
    route_id = booking_request.route_id if booking_request else payload.route_id

    if customer_id is None or route_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="customer_id and route_id are required when booking_request_id is not provided.",
        )

    return customer_id, route_id


def _validate_booking_request_against_payload(
    booking_request: BookingRequest,
    payload: TripCreate,
) -> None:
    if (
        payload.customer_id is not None
        and payload.customer_id != booking_request.customer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trip customer does not match the booking request customer.",
        )

    if payload.route_id is not None and payload.route_id != booking_request.route_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trip route does not match the booking request route.",
        )

    if payload.container_type != booking_request.container_type:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trip container type does not match the booking request.",
        )


def _ensure_booking_request_not_already_linked(
    db: Session,
    booking_request_id: UUID,
) -> None:
    existing_trip = db.scalar(
        select(Trip).where(Trip.booking_request_id == booking_request_id)
    )
    if existing_trip is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This booking request is already linked to a trip.",
        )


def _get_customer(db: Session, customer_id: UUID) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )
    return customer


def _get_route(db: Session, route_id: UUID) -> Route:
    route = db.get(Route, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return route


def _get_assignable_vehicle(
    db: Session,
    vehicle_id: UUID,
    exclude_trip_id: Optional[UUID] = None,
) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )

    has_other_active_trip = _resource_has_other_active_trip(
        db=db,
        field_name="assigned_vehicle_id",
        resource_id=vehicle_id,
        exclude_trip_id=exclude_trip_id,
    )
    if vehicle.status != VehicleStatus.AVAILABLE and not has_other_active_trip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is not available for assignment.",
        )
    if has_other_active_trip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is already assigned to another active trip.",
        )
    return vehicle


def _get_assignable_driver(
    db: Session,
    driver_id: UUID,
    exclude_trip_id: Optional[UUID] = None,
) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found.",
        )

    has_other_active_trip = _resource_has_other_active_trip(
        db=db,
        field_name="assigned_driver_id",
        resource_id=driver_id,
        exclude_trip_id=exclude_trip_id,
    )
    if driver.status != DriverStatus.AVAILABLE and not has_other_active_trip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver is not available for assignment.",
        )
    if has_other_active_trip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver is already assigned to another active trip.",
        )
    return driver


def _resource_has_other_active_trip(
    db: Session,
    field_name: str,
    resource_id: UUID,
    exclude_trip_id: Optional[UUID] = None,
) -> bool:
    column = getattr(Trip, field_name)
    statement = select(Trip.id).where(
        column == resource_id,
        Trip.status.in_(ACTIVE_TRIP_STATUSES),
    )
    if exclude_trip_id is not None:
        statement = statement.where(Trip.id != exclude_trip_id)

    return db.scalar(statement.limit(1)) is not None


def _resolve_route_amount(
    route: Route,
    container_type: BookingRequestContainerType,
) -> Decimal:
    if container_type == BookingRequestContainerType.CONTAINER_20FT:
        return route.price_20ft
    if container_type == BookingRequestContainerType.CONTAINER_30FT:
        return route.price_30ft
    if container_type == BookingRequestContainerType.CONTAINER_40FT:
        return route.price_40ft
    return route.price_double


def _resolve_trip_reference(
    db: Session,
    trip_reference: Optional[str],
) -> str:
    normalized_reference = (
        trip_reference.strip().upper()
        if trip_reference is not None
        else f"TRIP-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}"
    )
    _ensure_unique_trip_reference(db, normalized_reference)
    return normalized_reference


def _ensure_unique_trip_reference(db: Session, trip_reference: str) -> None:
    existing_trip = db.scalar(select(Trip).where(Trip.trip_reference == trip_reference))
    if existing_trip is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A trip with this reference already exists.",
        )


def _ensure_trip_is_mutable(trip: Trip) -> None:
    if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed or cancelled trips cannot be updated.",
        )


def _validate_milestone_transition(
    latest_milestone: Optional[TripMilestone],
    payload: TripMilestoneCreate,
) -> None:
    if latest_milestone is not None:
        if latest_milestone.status in (
            TripMilestoneStatus.BACK_AT_BASE,
            TripMilestoneStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No further milestones can be added to this trip.",
            )
        if (
            payload.recorded_at is not None
            and payload.recorded_at <= latest_milestone.recorded_at
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Milestone timestamps must move forward.",
            )

    if payload.status == TripMilestoneStatus.CANCELLED:
        return

    if latest_milestone is None:
        expected_status = ORDERED_TRIP_MILESTONES[0]
    else:
        current_index = ORDERED_TRIP_MILESTONES.index(latest_milestone.status)
        expected_status = ORDERED_TRIP_MILESTONES[current_index + 1]

    if payload.status != expected_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid milestone progression. Expected '{expected_status.value}'.",
        )


def _refresh_vehicle_status_for_trip_change(
    db: Session,
    current_vehicle_id: UUID,
    previous_vehicle_id: UUID,
    trip: Trip,
) -> None:
    current_vehicle = db.get(Vehicle, current_vehicle_id)
    if current_vehicle is not None and trip.status in ACTIVE_TRIP_STATUSES:
        current_vehicle.status = VehicleStatus.ON_TRIP
        db.add(current_vehicle)

    if previous_vehicle_id != current_vehicle_id:
        _refresh_vehicle_status(db, previous_vehicle_id)


def _refresh_driver_status_for_trip_change(
    db: Session,
    current_driver_id: UUID,
    previous_driver_id: UUID,
    trip: Trip,
) -> None:
    current_driver = db.get(Driver, current_driver_id)
    if current_driver is not None and trip.status in ACTIVE_TRIP_STATUSES:
        current_driver.status = DriverStatus.ON_TRIP
        db.add(current_driver)

    if previous_driver_id != current_driver_id:
        _refresh_driver_status(db, previous_driver_id)


def _refresh_vehicle_status(db: Session, vehicle_id: UUID) -> None:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        return
    if vehicle.status in (VehicleStatus.MAINTENANCE, VehicleStatus.INACTIVE):
        return

    has_active_trip = _resource_has_other_active_trip(
        db=db,
        field_name="assigned_vehicle_id",
        resource_id=vehicle_id,
    )
    vehicle.status = (
        VehicleStatus.ON_TRIP if has_active_trip else VehicleStatus.AVAILABLE
    )
    db.add(vehicle)


def _refresh_driver_status(db: Session, driver_id: UUID) -> None:
    driver = db.get(Driver, driver_id)
    if driver is None:
        return
    if driver.status == DriverStatus.INACTIVE:
        return

    has_active_trip = _resource_has_other_active_trip(
        db=db,
        field_name="assigned_driver_id",
        resource_id=driver_id,
    )
    driver.status = DriverStatus.ON_TRIP if has_active_trip else DriverStatus.AVAILABLE
    db.add(driver)


def _clean_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None
