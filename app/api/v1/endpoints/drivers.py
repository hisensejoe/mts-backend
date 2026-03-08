from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.driver import DriverStatus
from app.models.user import User
from app.schemas.driver import (
    DriverCreate,
    DriverDetailRead,
    DriverListFilters,
    DriverRead,
    DriverUpdate,
)
from app.services.driver import (
    create_driver,
    get_driver_detail,
    list_drivers,
    update_driver,
)

router = APIRouter(prefix="/drivers", tags=["drivers"])

AdminDriverAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_drivers(
    _: Annotated[User, AdminDriverAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    status: Optional[DriverStatus] = Query(default=None),
) -> PaginatedResponse[DriverRead]:
    filters = DriverListFilters(search=search, status=status)
    return list_drivers(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_driver_endpoint(
    payload: DriverCreate,
    _: Annotated[User, AdminDriverAccess],
    db: Annotated[Session, Depends(get_db)],
) -> DriverDetailRead:
    return create_driver(db=db, payload=payload)


@router.get("/{driver_id}")
def read_driver(
    driver_id: UUID,
    _: Annotated[User, AdminDriverAccess],
    db: Annotated[Session, Depends(get_db)],
) -> DriverDetailRead:
    return get_driver_detail(db=db, driver_id=driver_id)


@router.patch("/{driver_id}")
def update_driver_endpoint(
    driver_id: UUID,
    payload: DriverUpdate,
    _: Annotated[User, AdminDriverAccess],
    db: Annotated[Session, Depends(get_db)],
) -> DriverDetailRead:
    return update_driver(db=db, driver_id=driver_id, payload=payload)
