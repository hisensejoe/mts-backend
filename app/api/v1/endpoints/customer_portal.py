from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer_portal import (
    CustomerAvailableVehicleRead,
    CustomerOverviewRead,
    CustomerShipmentDetailRead,
    CustomerShipmentRead,
)
from app.services.customer_portal import (
    get_customer_overview,
    get_customer_shipment_detail,
    list_available_vehicles_for_customer,
    list_customer_shipments,
)

router = APIRouter(prefix="/customer", tags=["customer"])


@router.get("/overview")
def read_customer_overview(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerOverviewRead:
    return get_customer_overview(db=db, customer_user=current_user)


@router.get("/shipments")
def read_customer_shipments(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
) -> PaginatedResponse[CustomerShipmentRead]:
    return list_customer_shipments(
        db=db,
        customer_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/shipments/{trip_id}")
def read_customer_shipment_detail(
    trip_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerShipmentDetailRead:
    return get_customer_shipment_detail(
        db=db,
        customer_user=current_user,
        trip_id=trip_id,
    )


@router.get("/available-vehicles")
def read_customer_available_vehicles(
    _: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
) -> PaginatedResponse[CustomerAvailableVehicleRead]:
    return list_available_vehicles_for_customer(
        db=db,
        page=page,
        page_size=page_size,
    )
