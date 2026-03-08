from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.booking_request import (
    BookingRequest,
    BookingRequestContainerType,
    BookingRequestStatus,
)
from app.models.route import Route
from app.models.user import User
from app.schemas.booking_request import (
    BookingRequestAdminUpdate,
    BookingRequestCreate,
    BookingRequestDetailRead,
    BookingRequestListFilters,
    BookingRequestRead,
)


def list_booking_requests(
    db: Session,
    page: int,
    page_size: int,
    filters: BookingRequestListFilters,
) -> PaginatedResponse[BookingRequestRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(BookingRequest)
    count_statement = select(func.count()).select_from(BookingRequest)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            BookingRequest.pickup_location.ilike(pattern),
            BookingRequest.destination.ilike(pattern),
            BookingRequest.recipient_name.ilike(pattern),
            BookingRequest.recipient_phone.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.status is not None:
        statement = statement.where(BookingRequest.status == filters.status)
        count_statement = count_statement.where(BookingRequest.status == filters.status)

    if filters.customer_id is not None:
        statement = statement.where(BookingRequest.customer_id == filters.customer_id)
        count_statement = count_statement.where(
            BookingRequest.customer_id == filters.customer_id
        )

    total = db.scalar(count_statement) or 0
    booking_requests = db.scalars(
        statement.order_by(
            BookingRequest.preferred_pickup_date.desc(),
            BookingRequest.created_at.desc(),
        )
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [
        BookingRequestRead.model_validate(booking_request)
        for booking_request in booking_requests
    ]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def list_customer_booking_requests(
    db: Session,
    customer_user: User,
    page: int,
    page_size: int,
) -> PaginatedResponse[BookingRequestRead]:
    if customer_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer user is not linked to a customer account.",
        )

    return list_booking_requests(
        db=db,
        page=page,
        page_size=page_size,
        filters=BookingRequestListFilters(customer_id=customer_user.customer_id),
    )


def get_booking_request(db: Session, booking_request_id: UUID) -> BookingRequest:
    booking_request = db.get(BookingRequest, booking_request_id)
    if booking_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found.",
        )
    return booking_request


def get_booking_request_detail(
    db: Session,
    booking_request_id: UUID,
) -> BookingRequestDetailRead:
    booking_request = get_booking_request(db, booking_request_id)
    return BookingRequestDetailRead.model_validate(booking_request)


def get_customer_booking_request_detail(
    db: Session,
    customer_user: User,
    booking_request_id: UUID,
) -> BookingRequestDetailRead:
    booking_request = get_booking_request(db, booking_request_id)
    if booking_request.customer_id != customer_user.customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found.",
        )
    return BookingRequestDetailRead.model_validate(booking_request)


def create_booking_request_for_customer(
    db: Session,
    customer_user: User,
    payload: BookingRequestCreate,
) -> BookingRequestDetailRead:
    if customer_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer user is not linked to a customer account.",
        )

    pickup_location = payload.pickup_location.strip()
    destination = payload.destination.strip()
    route = _get_route_by_origin_destination(db, pickup_location, destination)
    quoted_amount = _resolve_quote(route, payload.container_type)

    booking_request = BookingRequest(
        customer_id=customer_user.customer_id,
        requested_by_user_id=customer_user.id,
        route_id=route.id,
        pickup_location=pickup_location,
        destination=destination,
        container_type=payload.container_type,
        weight_tonnes=payload.weight_tonnes,
        preferred_pickup_date=payload.preferred_pickup_date,
        preferred_pickup_time=payload.preferred_pickup_time,
        delivery_address=payload.delivery_address.strip(),
        recipient_name=payload.recipient_name.strip(),
        recipient_phone=payload.recipient_phone,
        notes=_clean_optional_string(payload.notes),
        status=BookingRequestStatus.PENDING,
        quoted_amount=quoted_amount,
    )
    db.add(booking_request)
    db.commit()
    db.refresh(booking_request)
    return BookingRequestDetailRead.model_validate(booking_request)


def update_booking_request_status(
    db: Session,
    booking_request_id: UUID,
    payload: BookingRequestAdminUpdate,
) -> BookingRequestDetailRead:
    booking_request = get_booking_request(db, booking_request_id)
    booking_request.status = payload.status
    db.add(booking_request)
    db.commit()
    db.refresh(booking_request)
    return BookingRequestDetailRead.model_validate(booking_request)


def _get_route_by_origin_destination(
    db: Session,
    origin: str,
    destination: str,
) -> Route:
    route = db.scalar(
        select(Route).where(Route.origin == origin, Route.destination == destination)
    )
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No configured route matches this pickup and destination.",
        )
    return route


def _resolve_quote(
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


def _clean_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None
