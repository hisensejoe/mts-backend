from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailRead,
    CustomerListFilters,
    CustomerRead,
    CustomerUpdate,
)
from app.services.customer import (
    create_customer,
    get_customer_detail,
    list_customers,
    update_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])

AdminCustomerAccess = Depends(require_roles("super_admin", "operations_manager"))


@router.get("")
def read_customers(
    _: Annotated[User, AdminCustomerAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
) -> PaginatedResponse[CustomerRead]:
    filters = CustomerListFilters(search=search, is_active=is_active)
    return list_customers(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_customer_endpoint(
    payload: CustomerCreate,
    _: Annotated[User, AdminCustomerAccess],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerDetailRead:
    return create_customer(db=db, payload=payload)


@router.get("/{customer_id}")
def read_customer(
    customer_id: UUID,
    _: Annotated[User, AdminCustomerAccess],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerDetailRead:
    return get_customer_detail(db=db, customer_id=customer_id)


@router.patch("/{customer_id}")
def update_customer_endpoint(
    customer_id: UUID,
    payload: CustomerUpdate,
    _: Annotated[User, AdminCustomerAccess],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerDetailRead:
    return update_customer(db=db, customer_id=customer_id, payload=payload)
