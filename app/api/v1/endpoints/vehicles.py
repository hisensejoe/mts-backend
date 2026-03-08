from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import VehicleStatus
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleDetailRead,
    VehicleListFilters,
    VehicleRead,
    VehicleUpdate,
)
from app.services.vehicle import (
    create_vehicle,
    get_vehicle_detail,
    list_vehicles,
    update_vehicle,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

AdminVehicleAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_vehicles(
    _: Annotated[User, AdminVehicleAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    status: Optional[VehicleStatus] = Query(default=None),
    assigned_driver_id: Optional[UUID] = Query(default=None),
) -> PaginatedResponse[VehicleRead]:
    filters = VehicleListFilters(
        search=search,
        status=status,
        assigned_driver_id=assigned_driver_id,
    )
    return list_vehicles(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_vehicle_endpoint(
    payload: VehicleCreate,
    _: Annotated[User, AdminVehicleAccess],
    db: Annotated[Session, Depends(get_db)],
) -> VehicleDetailRead:
    return create_vehicle(db=db, payload=payload)


@router.get(
    "/{vehicle_id}",
)
def read_vehicle(
    vehicle_id: UUID,
    _: Annotated[User, AdminVehicleAccess],
    db: Annotated[Session, Depends(get_db)],
) -> VehicleDetailRead:
    return get_vehicle_detail(db=db, vehicle_id=vehicle_id)


@router.patch(
    "/{vehicle_id}",
)
def update_vehicle_endpoint(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    _: Annotated[User, AdminVehicleAccess],
    db: Annotated[Session, Depends(get_db)],
) -> VehicleDetailRead:
    return update_vehicle(db=db, vehicle_id=vehicle_id, payload=payload)
