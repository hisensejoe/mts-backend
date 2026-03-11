from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.trip import TripStatus
from app.models.user import User
from app.schemas.trip import (
    TripCreate,
    TripDetailRead,
    TripListFilters,
    TripMilestoneCreate,
    TripRead,
    TripUpdate,
)
from app.services.trip import (
    add_trip_milestone,
    create_trip,
    get_trip_detail,
    list_trips,
    update_trip,
)

router = APIRouter(prefix="/trips", tags=["trips"])

AdminTripAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_trips(
    _: Annotated[User, AdminTripAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    status: Optional[TripStatus] = Query(default=None),
    customer_id: Optional[UUID] = Query(default=None),
    assigned_vehicle_id: Optional[UUID] = Query(default=None),
    assigned_driver_id: Optional[UUID] = Query(default=None),
) -> PaginatedResponse[TripRead]:
    filters = TripListFilters(
        search=search,
        status=status,
        customer_id=customer_id,
        assigned_vehicle_id=assigned_vehicle_id,
        assigned_driver_id=assigned_driver_id,
    )
    return list_trips(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_trip_endpoint(
    payload: TripCreate,
    current_user: Annotated[User, AdminTripAccess],
    db: Annotated[Session, Depends(get_db)],
) -> TripDetailRead:
    return create_trip(db=db, current_user=current_user, payload=payload)


@router.get("/{trip_id}")
def read_trip(
    trip_id: UUID,
    _: Annotated[User, AdminTripAccess],
    db: Annotated[Session, Depends(get_db)],
) -> TripDetailRead:
    return get_trip_detail(db=db, trip_id=trip_id)


@router.patch("/{trip_id}")
def update_trip_endpoint(
    trip_id: UUID,
    payload: TripUpdate,
    _: Annotated[User, AdminTripAccess],
    db: Annotated[Session, Depends(get_db)],
) -> TripDetailRead:
    return update_trip(db=db, trip_id=trip_id, payload=payload)


@router.post("/{trip_id}/milestones", status_code=201)
def add_trip_milestone_endpoint(
    trip_id: UUID,
    payload: TripMilestoneCreate,
    current_user: Annotated[User, AdminTripAccess],
    db: Annotated[Session, Depends(get_db)],
) -> TripDetailRead:
    return add_trip_milestone(
        db=db,
        trip_id=trip_id,
        current_user=current_user,
        payload=payload,
    )
