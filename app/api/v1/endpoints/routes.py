from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.pagination import PaginatedResponse
from app.db.session import get_db
from app.models.route import RouteType
from app.models.user import User
from app.schemas.route import (
    RouteCreate,
    RouteDetailRead,
    RouteListFilters,
    RouteRead,
    RouteUpdate,
)
from app.services.route import create_route, get_route_detail, list_routes, update_route

router = APIRouter(prefix="/routes", tags=["routes"])

AdminRouteAccess = Depends(require_roles("super_admin", "operations_manager"))


@router.get("")
def read_routes(
    _: Annotated[User, AdminRouteAccess],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1),
    search: Optional[str] = Query(default=None),
    route_type: Optional[RouteType] = Query(default=None),
) -> PaginatedResponse[RouteRead]:
    filters = RouteListFilters(search=search, route_type=route_type)
    return list_routes(db=db, page=page, page_size=page_size, filters=filters)


@router.post("", status_code=201)
def create_route_endpoint(
    payload: RouteCreate,
    _: Annotated[User, AdminRouteAccess],
    db: Annotated[Session, Depends(get_db)],
) -> RouteDetailRead:
    return create_route(db=db, payload=payload)


@router.get("/{route_id}")
def read_route(
    route_id: UUID,
    _: Annotated[User, AdminRouteAccess],
    db: Annotated[Session, Depends(get_db)],
) -> RouteDetailRead:
    return get_route_detail(db=db, route_id=route_id)


@router.patch("/{route_id}")
def update_route_endpoint(
    route_id: UUID,
    payload: RouteUpdate,
    _: Annotated[User, AdminRouteAccess],
    db: Annotated[Session, Depends(get_db)],
) -> RouteDetailRead:
    return update_route(db=db, route_id=route_id, payload=payload)
