from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.expense import ExpenseType


class ExpenseBase(BaseModel):
    trip_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    expense_type: ExpenseType
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    expense_date: datetime
    vendor_name: Optional[str] = Field(default=None, max_length=255)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    description: Optional[str] = Field(default=None, min_length=1, max_length=255)
    expense_date: Optional[datetime] = None
    vendor_name: Optional[str] = Field(default=None, max_length=255)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ExpenseRead(BaseModel):
    id: UUID
    trip_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    recorded_by_user_id: Optional[UUID] = None
    expense_type: ExpenseType
    amount: Decimal
    description: str
    expense_date: datetime
    vendor_name: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExpenseListFilters(BaseModel):
    expense_type: Optional[ExpenseType] = None
    trip_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    search: Optional[str] = None
