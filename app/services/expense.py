from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.driver import Driver
from app.models.expense import Expense, ExpenseType
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseListFilters,
    ExpenseRead,
    ExpenseUpdate,
)


def list_expenses(
    db: Session,
    page: int,
    page_size: int,
    filters: ExpenseListFilters,
) -> PaginatedResponse[ExpenseRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Expense)
    count_statement = select(func.count()).select_from(Expense)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Expense.description.ilike(pattern),
            Expense.vendor_name.ilike(pattern),
            Expense.reference_number.ilike(pattern),
            Expense.notes.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.expense_type is not None:
        statement = statement.where(Expense.expense_type == filters.expense_type)
        count_statement = count_statement.where(
            Expense.expense_type == filters.expense_type
        )

    if filters.trip_id is not None:
        statement = statement.where(Expense.trip_id == filters.trip_id)
        count_statement = count_statement.where(Expense.trip_id == filters.trip_id)

    if filters.vehicle_id is not None:
        statement = statement.where(Expense.vehicle_id == filters.vehicle_id)
        count_statement = count_statement.where(
            Expense.vehicle_id == filters.vehicle_id
        )

    if filters.driver_id is not None:
        statement = statement.where(Expense.driver_id == filters.driver_id)
        count_statement = count_statement.where(Expense.driver_id == filters.driver_id)

    total = db.scalar(count_statement) or 0
    expenses = db.scalars(
        statement.order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [_build_expense_read(expense) for expense in expenses]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_expense(db: Session, expense_id: UUID) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )
    return expense


def get_expense_detail(db: Session, expense_id: UUID) -> ExpenseRead:
    expense = get_expense(db, expense_id)
    return _build_expense_read(expense)


def create_expense(
    db: Session,
    current_user: User,
    payload: ExpenseCreate,
) -> ExpenseRead:
    trip = _resolve_trip(db, payload.trip_id)
    vehicle = _resolve_vehicle(db, payload.vehicle_id)
    driver = _resolve_driver(db, payload.driver_id)
    _validate_expense_links(
        expense_type=payload.expense_type,
        trip=trip,
        vehicle=vehicle,
        driver=driver,
    )

    if trip is not None:
        if vehicle is None:
            vehicle = db.get(Vehicle, trip.assigned_vehicle_id)
        if driver is None:
            driver = db.get(Driver, trip.assigned_driver_id)

    expense = Expense(
        trip_id=trip.id if trip else None,
        vehicle_id=vehicle.id if vehicle else None,
        driver_id=driver.id if driver else None,
        recorded_by_user_id=current_user.id,
        expense_type=payload.expense_type,
        amount=payload.amount,
        description=payload.description.strip(),
        expense_date=payload.expense_date,
        vendor_name=_clean_optional_string(payload.vendor_name),
        reference_number=_clean_optional_string(payload.reference_number),
        notes=_clean_optional_string(payload.notes),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _build_expense_read(expense)


def update_expense(
    db: Session,
    expense_id: UUID,
    payload: ExpenseUpdate,
) -> ExpenseRead:
    expense = get_expense(db, expense_id)
    changes = payload.model_dump(exclude_unset=True)

    if "trip_id" in changes:
        expense.trip_id = changes["trip_id"]
    if "vehicle_id" in changes:
        expense.vehicle_id = changes["vehicle_id"]
    if "driver_id" in changes:
        expense.driver_id = changes["driver_id"]
    if "amount" in changes and changes["amount"] is not None:
        expense.amount = changes["amount"]
    if "description" in changes and changes["description"] is not None:
        expense.description = changes["description"].strip()
    if "expense_date" in changes and changes["expense_date"] is not None:
        expense.expense_date = changes["expense_date"]
    if "vendor_name" in changes:
        expense.vendor_name = _clean_optional_string(changes["vendor_name"])
    if "reference_number" in changes:
        expense.reference_number = _clean_optional_string(changes["reference_number"])
    if "notes" in changes:
        expense.notes = _clean_optional_string(changes["notes"])

    trip = _resolve_trip(db, expense.trip_id)
    vehicle = _resolve_vehicle(db, expense.vehicle_id)
    driver = _resolve_driver(db, expense.driver_id)
    _validate_expense_links(
        expense_type=expense.expense_type,
        trip=trip,
        vehicle=vehicle,
        driver=driver,
    )

    if trip is not None:
        if vehicle is None:
            expense.vehicle_id = trip.assigned_vehicle_id
            vehicle = db.get(Vehicle, trip.assigned_vehicle_id)
        if driver is None:
            expense.driver_id = trip.assigned_driver_id
            driver = db.get(Driver, trip.assigned_driver_id)

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _build_expense_read(expense)


def _build_expense_read(expense: Expense) -> ExpenseRead:
    return ExpenseRead(
        id=expense.id,
        trip_id=expense.trip_id,
        vehicle_id=expense.vehicle_id,
        driver_id=expense.driver_id,
        recorded_by_user_id=expense.recorded_by_user_id,
        expense_type=expense.expense_type,
        amount=expense.amount,
        description=expense.description,
        expense_date=expense.expense_date,
        vendor_name=expense.vendor_name,
        reference_number=expense.reference_number,
        notes=expense.notes,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def _resolve_trip(db: Session, trip_id: Optional[UUID]) -> Optional[Trip]:
    if trip_id is None:
        return None
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found.",
        )
    return trip


def _resolve_vehicle(db: Session, vehicle_id: Optional[UUID]) -> Optional[Vehicle]:
    if vehicle_id is None:
        return None
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )
    return vehicle


def _resolve_driver(db: Session, driver_id: Optional[UUID]) -> Optional[Driver]:
    if driver_id is None:
        return None
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found.",
        )
    return driver


def _validate_expense_links(
    expense_type: ExpenseType,
    trip: Optional[Trip],
    vehicle: Optional[Vehicle],
    driver: Optional[Driver],
) -> None:
    if expense_type == ExpenseType.MAINTENANCE:
        if trip is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Maintenance expenses must not be linked to a trip.",
            )
        if vehicle is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="vehicle_id is required for maintenance expenses.",
            )
        return

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="trip_id is required for fuel, per diem, and toll expenses.",
        )

    if vehicle is not None and vehicle.id != trip.assigned_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Expense vehicle does not match the trip assignment.",
        )

    if driver is not None and driver.id != trip.assigned_driver_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Expense driver does not match the trip assignment.",
        )


def _clean_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None
