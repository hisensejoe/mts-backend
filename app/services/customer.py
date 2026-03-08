from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.core.security import normalize_phone
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailRead,
    CustomerListFilters,
    CustomerRead,
    CustomerUpdate,
)


def list_customers(
    db: Session,
    page: int,
    page_size: int,
    filters: CustomerListFilters,
) -> PaginatedResponse[CustomerRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Customer)
    count_statement = select(func.count()).select_from(Customer)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Customer.company_name.ilike(pattern),
            Customer.contact_name.ilike(pattern),
            Customer.contact_phone.ilike(pattern),
            Customer.contact_email.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.is_active is not None:
        statement = statement.where(Customer.is_active == filters.is_active)
        count_statement = count_statement.where(Customer.is_active == filters.is_active)

    total = db.scalar(count_statement) or 0
    customers = db.scalars(
        statement.order_by(Customer.company_name, Customer.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [CustomerRead.model_validate(customer) for customer in customers]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_customer(db: Session, customer_id: UUID) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )
    return customer


def get_customer_detail(db: Session, customer_id: UUID) -> CustomerDetailRead:
    customer = get_customer(db, customer_id)
    return CustomerDetailRead.model_validate(customer)


def create_customer(db: Session, payload: CustomerCreate) -> CustomerDetailRead:
    normalized_company_name = payload.company_name.strip()
    _ensure_unique_company_name(db, normalized_company_name)

    customer = Customer(
        company_name=normalized_company_name,
        contact_name=_clean_optional_string(payload.contact_name),
        contact_phone=_normalize_optional_phone(payload.contact_phone),
        contact_email=_normalize_optional_email(payload.contact_email),
        is_active=payload.is_active,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return CustomerDetailRead.model_validate(customer)


def update_customer(
    db: Session,
    customer_id: UUID,
    payload: CustomerUpdate,
) -> CustomerDetailRead:
    customer = get_customer(db, customer_id)
    changes = payload.model_dump(exclude_unset=True)

    if "company_name" in changes and changes["company_name"] is not None:
        company_name = changes["company_name"].strip()
        _ensure_unique_company_name(
            db,
            company_name,
            exclude_customer_id=customer.id,
        )
        changes["company_name"] = company_name

    if "contact_name" in changes:
        changes["contact_name"] = _clean_optional_string(changes["contact_name"])

    if "contact_phone" in changes:
        changes["contact_phone"] = _normalize_optional_phone(changes["contact_phone"])

    if "contact_email" in changes:
        changes["contact_email"] = _normalize_optional_email(changes["contact_email"])

    for field_name, value in changes.items():
        setattr(customer, field_name, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return CustomerDetailRead.model_validate(customer)


def _ensure_unique_company_name(
    db: Session,
    company_name: str,
    exclude_customer_id: Optional[UUID] = None,
) -> None:
    statement = select(Customer).where(Customer.company_name == company_name)
    if exclude_customer_id is not None:
        statement = statement.where(Customer.id != exclude_customer_id)

    existing_customer = db.scalar(statement)
    if existing_customer is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this company name already exists.",
        )


def _clean_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _normalize_optional_phone(value: Optional[str]) -> Optional[str]:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    return normalize_phone(cleaned)


def _normalize_optional_email(value: Optional[str]) -> Optional[str]:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None
    return cleaned.lower()
