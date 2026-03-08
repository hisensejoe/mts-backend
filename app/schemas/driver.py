from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.driver import DriverStatus


class DriverBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=10, max_length=20)
    license_number: str = Field(min_length=3, max_length=100)
    rating: Optional[Decimal] = Field(default=None, ge=0, le=5)
    per_diem: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    status: DriverStatus = DriverStatus.AVAILABLE


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    license_number: Optional[str] = Field(default=None, min_length=3, max_length=100)
    rating: Optional[Decimal] = Field(default=None, ge=0, le=5)
    per_diem: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    status: Optional[DriverStatus] = None


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    phone: str
    license_number: str
    trip_count: int
    rating: Optional[Decimal] = None
    per_diem: Optional[Decimal] = None
    status: DriverStatus


class DriverDetailRead(DriverRead):
    created_at: datetime
    updated_at: datetime


class DriverListFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[DriverStatus] = None
