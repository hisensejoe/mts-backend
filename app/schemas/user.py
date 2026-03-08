from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None


class CustomerSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    full_name: str
    status: str
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    role: RoleRead
    customer: Optional[CustomerSummaryRead] = None
    created_at: datetime
    updated_at: datetime
