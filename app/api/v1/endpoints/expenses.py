from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.expense import ExpenseType
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseListFilters,
    ExpenseRead,
    ExpenseUpdate,
)
from app.services.expense import (
    create_expense,
    get_expense_detail,
    list_expenses,
    update_expense,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])

AdminExpenseAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_expenses(
    _: Annotated[User, AdminExpenseAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    expense_type: Optional[ExpenseType] = Query(default=None),
    trip_id: Optional[UUID] = Query(default=None),
    vehicle_id: Optional[UUID] = Query(default=None),
    driver_id: Optional[UUID] = Query(default=None),
) -> PaginatedResponse[ExpenseRead]:
    filters = ExpenseListFilters(
        search=search,
        expense_type=expense_type,
        trip_id=trip_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
    )
    return list_expenses(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_expense_endpoint(
    payload: ExpenseCreate,
    current_user: Annotated[User, AdminExpenseAccess],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    return create_expense(db=db, current_user=current_user, payload=payload)


@router.get("/{expense_id}")
def read_expense(
    expense_id: UUID,
    _: Annotated[User, AdminExpenseAccess],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    return get_expense_detail(db=db, expense_id=expense_id)


@router.patch("/{expense_id}")
def update_expense_endpoint(
    expense_id: UUID,
    payload: ExpenseUpdate,
    _: Annotated[User, AdminExpenseAccess],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    return update_expense(db=db, expense_id=expense_id, payload=payload)
