from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    contact_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    contact_phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    contact_phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool


class CustomerDetailRead(CustomerRead):
    created_at: datetime
    updated_at: datetime


class CustomerListFilters(BaseModel):
    search: Optional[str] = None
    is_active: Optional[bool] = None
