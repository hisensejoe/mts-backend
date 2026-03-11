from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.vehicle import VehicleStatus
from app.schemas.driver import DriverRead


class VehicleBase(BaseModel):
    registration_number: str = Field(min_length=3, max_length=50)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    manufacture_year: int = Field(ge=1900, le=2100)
    body_type: str = Field(min_length=1, max_length=100)
    fuel_type: str = Field(min_length=1, max_length=50)
    odometer_km: int = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    assigned_driver_id: Optional[UUID] = None


class VehicleCreate(VehicleBase):
    make: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    body_type: Optional[str] = Field(default=None, max_length=100)


class VehicleUpdate(BaseModel):
    registration_number: Optional[str] = Field(
        default=None, min_length=3, max_length=50
    )
    make: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model: Optional[str] = Field(default=None, min_length=1, max_length=100)
    manufacture_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    body_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    fuel_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    odometer_km: Optional[int] = Field(default=None, ge=0)
    status: Optional[VehicleStatus] = None
    assigned_driver_id: Optional[UUID] = None


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_number: str
    make: str
    model: str
    manufacture_year: int
    body_type: str
    fuel_type: str
    odometer_km: int
    status: VehicleStatus
    assigned_driver_id: Optional[UUID] = None


class VehicleDetailRead(VehicleRead):
    assigned_driver: Optional[DriverRead] = None
    created_at: datetime
    updated_at: datetime


class VehicleListFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[VehicleStatus] = None
    assigned_driver_id: Optional[UUID] = None
