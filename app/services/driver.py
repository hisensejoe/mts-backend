from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.driver import Driver
from app.schemas.driver import (
    DriverCreate,
    DriverDetailRead,
    DriverListFilters,
    DriverRead,
    DriverUpdate,
)


def list_drivers(
    db: Session,
    page: int,
    page_size: int,
    filters: DriverListFilters,
) -> PaginatedResponse[DriverRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Driver)
    count_statement = select(func.count()).select_from(Driver)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Driver.full_name.ilike(pattern),
            Driver.phone.ilike(pattern),
            Driver.license_number.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.status is not None:
        statement = statement.where(Driver.status == filters.status)
        count_statement = count_statement.where(Driver.status == filters.status)

    total = db.scalar(count_statement) or 0
    drivers = db.scalars(
        statement.order_by(Driver.full_name, Driver.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [DriverRead.model_validate(driver) for driver in drivers]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_driver(db: Session, driver_id: UUID) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found.",
        )
    return driver


def get_driver_detail(db: Session, driver_id: UUID) -> DriverDetailRead:
    driver = get_driver(db, driver_id)
    return DriverDetailRead.model_validate(driver)


def create_driver(db: Session, payload: DriverCreate) -> DriverDetailRead:
    normalized_phone = payload.phone
    normalized_license_number = payload.license_number.strip()
    _ensure_unique_phone(db, normalized_phone)
    _ensure_unique_license_number(db, normalized_license_number)

    driver = Driver(
        full_name=payload.full_name.strip(),
        phone=normalized_phone,
        license_number=normalized_license_number,
        rating=payload.rating,
        per_diem=payload.per_diem,
        status=payload.status,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return DriverDetailRead.model_validate(driver)


def update_driver(
    db: Session, driver_id: UUID, payload: DriverUpdate
) -> DriverDetailRead:
    driver = get_driver(db, driver_id)
    changes = payload.model_dump(exclude_unset=True)

    if "phone" in changes and changes["phone"] is not None:
        normalized_phone = changes["phone"]
        _ensure_unique_phone(db, normalized_phone, exclude_driver_id=driver.id)
        changes["phone"] = normalized_phone

    if "license_number" in changes and changes["license_number"] is not None:
        license_number = changes["license_number"].strip()
        _ensure_unique_license_number(
            db,
            license_number,
            exclude_driver_id=driver.id,
        )
        changes["license_number"] = license_number

    if "full_name" in changes and changes["full_name"] is not None:
        changes["full_name"] = changes["full_name"].strip()

    for field_name, value in changes.items():
        setattr(driver, field_name, value)

    db.add(driver)
    db.commit()
    db.refresh(driver)
    return DriverDetailRead.model_validate(driver)


def _ensure_unique_phone(
    db: Session,
    phone: str,
    exclude_driver_id: Optional[UUID] = None,
) -> None:
    statement = select(Driver).where(Driver.phone == phone)
    if exclude_driver_id is not None:
        statement = statement.where(Driver.id != exclude_driver_id)

    existing_driver = db.scalar(statement)
    if existing_driver is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A driver with this phone already exists.",
        )


def _ensure_unique_license_number(
    db: Session,
    license_number: str,
    exclude_driver_id: Optional[UUID] = None,
) -> None:
    statement = select(Driver).where(Driver.license_number == license_number)
    if exclude_driver_id is not None:
        statement = statement.where(Driver.id != exclude_driver_id)

    existing_driver = db.scalar(statement)
    if existing_driver is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A driver with this license number already exists.",
        )
