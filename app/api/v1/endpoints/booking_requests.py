from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.booking_request import BookingRequestStatus
from app.models.user import User
from app.schemas.booking_request import (
    BookingRequestAdminUpdate,
    BookingRequestCreate,
    BookingRequestDetailRead,
    BookingRequestListFilters,
    BookingRequestRead,
)
from app.services.booking_request import (
    create_booking_request_for_customer,
    get_booking_request_detail,
    get_customer_booking_request_detail,
    list_booking_requests,
    list_customer_booking_requests,
    update_booking_request_status,
)

router = APIRouter(prefix="/booking-requests", tags=["booking-requests"])
customer_router = APIRouter(
    prefix="/customer/booking-requests",
    tags=["customer-booking-requests"],
)

AdminBookingRequestAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_booking_requests(
    _: Annotated[User, AdminBookingRequestAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    status: Optional[BookingRequestStatus] = Query(default=None),
    customer_id: Optional[UUID] = Query(default=None),
) -> PaginatedResponse[BookingRequestRead]:
    filters = BookingRequestListFilters(
        search=search,
        status=status,
        customer_id=customer_id,
    )
    return list_booking_requests(db=db, page=page, page_size=page_size, filters=filters)


@router.get("/{booking_request_id}")
def read_booking_request(
    booking_request_id: UUID,
    _: Annotated[User, AdminBookingRequestAccess],
    db: Annotated[Session, Depends(get_db)],
) -> BookingRequestDetailRead:
    return get_booking_request_detail(db=db, booking_request_id=booking_request_id)


@router.patch("/{booking_request_id}")
def update_booking_request_endpoint(
    booking_request_id: UUID,
    payload: BookingRequestAdminUpdate,
    _: Annotated[User, AdminBookingRequestAccess],
    db: Annotated[Session, Depends(get_db)],
) -> BookingRequestDetailRead:
    return update_booking_request_status(
        db=db,
        booking_request_id=booking_request_id,
        payload=payload,
    )


@customer_router.get("")
def read_my_booking_requests(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
) -> PaginatedResponse[BookingRequestRead]:
    return list_customer_booking_requests(
        db=db,
        customer_user=current_user,
        page=page,
        page_size=page_size,
    )


@customer_router.post("", status_code=201)
def create_my_booking_request(
    payload: BookingRequestCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BookingRequestDetailRead:
    return create_booking_request_for_customer(
        db=db,
        customer_user=current_user,
        payload=payload,
    )


@customer_router.get("/{booking_request_id}")
def read_my_booking_request(
    booking_request_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BookingRequestDetailRead:
    return get_customer_booking_request_detail(
        db=db,
        customer_user=current_user,
        booking_request_id=booking_request_id,
    )
