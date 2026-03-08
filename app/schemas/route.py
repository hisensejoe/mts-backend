from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.route import RouteType


class RouteBase(BaseModel):
    origin: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    distance_km: int = Field(ge=0)
    route_type: RouteType = RouteType.DOMESTIC
    price_20ft: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    price_30ft: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    price_40ft: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    price_double: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    origin: Optional[str] = Field(default=None, min_length=1, max_length=255)
    destination: Optional[str] = Field(default=None, min_length=1, max_length=255)
    distance_km: Optional[int] = Field(default=None, ge=0)
    route_type: Optional[RouteType] = None
    price_20ft: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    price_30ft: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    price_40ft: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    price_double: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    origin: str
    destination: str
    distance_km: int
    route_type: RouteType
    price_20ft: Decimal
    price_30ft: Decimal
    price_40ft: Decimal
    price_double: Decimal


class RouteDetailRead(RouteRead):
    created_at: datetime
    updated_at: datetime


class RouteListFilters(BaseModel):
    search: Optional[str] = None
    route_type: Optional[RouteType] = None
