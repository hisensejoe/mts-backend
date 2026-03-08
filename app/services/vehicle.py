from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleDetailRead,
    VehicleListFilters,
    VehicleRead,
    VehicleUpdate,
)


def list_vehicles(
    db: Session,
    page: int,
    page_size: int,
    filters: VehicleListFilters,
) -> PaginatedResponse[VehicleRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Vehicle)
    count_statement = select(func.count()).select_from(Vehicle)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Vehicle.registration_number.ilike(pattern),
            Vehicle.make.ilike(pattern),
            Vehicle.model.ilike(pattern),
            Vehicle.body_type.ilike(pattern),
            Vehicle.fuel_type.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.status is not None:
        statement = statement.where(Vehicle.status == filters.status)
        count_statement = count_statement.where(Vehicle.status == filters.status)

    if filters.assigned_driver_id is not None:
        statement = statement.where(
            Vehicle.assigned_driver_id == filters.assigned_driver_id
        )
        count_statement = count_statement.where(
            Vehicle.assigned_driver_id == filters.assigned_driver_id
        )

    total = db.scalar(count_statement) or 0
    vehicles = db.scalars(
        statement.order_by(Vehicle.registration_number, Vehicle.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [VehicleRead.model_validate(vehicle) for vehicle in vehicles]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_vehicle(db: Session, vehicle_id: UUID) -> Vehicle:
    vehicle = db.scalar(
        select(Vehicle)
        .options(joinedload(Vehicle.assigned_driver))
        .where(Vehicle.id == vehicle_id)
    )
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )
    return vehicle


def get_vehicle_detail(db: Session, vehicle_id: UUID) -> VehicleDetailRead:
    vehicle = get_vehicle(db, vehicle_id)
    return VehicleDetailRead.model_validate(vehicle)


def create_vehicle(db: Session, payload: VehicleCreate) -> VehicleDetailRead:
    normalized_registration_number = payload.registration_number.strip().upper()
    _ensure_unique_registration_number(db, normalized_registration_number)
    assigned_driver = _resolve_assigned_driver(db, payload.assigned_driver_id)

    vehicle = Vehicle(
        registration_number=normalized_registration_number,
        make=payload.make.strip(),
        model=payload.model.strip(),
        manufacture_year=payload.manufacture_year,
        body_type=payload.body_type.strip(),
        fuel_type=payload.fuel_type.strip(),
        odometer_km=payload.odometer_km,
        status=payload.status,
        assigned_driver_id=assigned_driver.id if assigned_driver else None,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return get_vehicle_detail(db, vehicle.id)


def update_vehicle(
    db: Session,
    vehicle_id: UUID,
    payload: VehicleUpdate,
) -> VehicleDetailRead:
    vehicle = get_vehicle(db, vehicle_id)
    changes = payload.model_dump(exclude_unset=True)

    if "registration_number" in changes and changes["registration_number"] is not None:
        registration_number = changes["registration_number"].strip().upper()
        _ensure_unique_registration_number(
            db,
            registration_number,
            exclude_vehicle_id=vehicle.id,
        )
        changes["registration_number"] = registration_number

    if "assigned_driver_id" in changes:
        assigned_driver = _resolve_assigned_driver(db, changes["assigned_driver_id"])
        changes["assigned_driver_id"] = assigned_driver.id if assigned_driver else None

    for field_name in ("make", "model", "body_type", "fuel_type"):
        if field_name in changes and changes[field_name] is not None:
            changes[field_name] = changes[field_name].strip()

    for field_name, value in changes.items():
        setattr(vehicle, field_name, value)

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return get_vehicle_detail(db, vehicle.id)


def _resolve_assigned_driver(
    db: Session,
    assigned_driver_id: Optional[UUID],
) -> Optional[Driver]:
    if assigned_driver_id is None:
        return None

    driver = db.get(Driver, assigned_driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned driver not found.",
        )

    return driver


def _ensure_unique_registration_number(
    db: Session,
    registration_number: str,
    exclude_vehicle_id: Optional[UUID] = None,
) -> None:
    statement = select(Vehicle).where(
        Vehicle.registration_number == registration_number
    )
    if exclude_vehicle_id is not None:
        statement = statement.where(Vehicle.id != exclude_vehicle_id)

    existing_vehicle = db.scalar(statement)
    if existing_vehicle is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vehicle with this registration number already exists.",
        )
