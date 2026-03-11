from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryRead
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

AdminDashboardAccess = Depends(
    require_roles("super_admin", "operations_manager", "dispatcher")
)


@router.get("")
def read_dashboard(
    _: Annotated[User, AdminDashboardAccess],
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummaryRead:
    return get_dashboard_summary(db=db)
