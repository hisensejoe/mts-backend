from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.pagination import PaginatedResponse, build_paginated_response, paginate
from app.models.route import Route
from app.schemas.route import (
    RouteCreate,
    RouteDetailRead,
    RouteListFilters,
    RouteRead,
    RouteUpdate,
)


def list_routes(
    db: Session,
    page: int,
    page_size: int,
    filters: RouteListFilters,
) -> PaginatedResponse[RouteRead]:
    settings = get_settings()
    pagination = paginate(
        page=page, page_size=page_size, max_page_size=settings.max_page_size
    )

    statement = select(Route)
    count_statement = select(func.count()).select_from(Route)

    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        predicate = or_(
            Route.origin.ilike(pattern),
            Route.destination.ilike(pattern),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    if filters.route_type is not None:
        statement = statement.where(Route.route_type == filters.route_type)
        count_statement = count_statement.where(Route.route_type == filters.route_type)

    total = db.scalar(count_statement) or 0
    routes = db.scalars(
        statement.order_by(Route.origin, Route.destination, Route.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = [RouteRead.model_validate(route) for route in routes]
    return build_paginated_response(items=items, total=total, pagination=pagination)


def get_route(db: Session, route_id: UUID) -> Route:
    route = db.get(Route, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return route


def get_route_detail(db: Session, route_id: UUID) -> RouteDetailRead:
    route = get_route(db, route_id)
    return RouteDetailRead.model_validate(route)


def create_route(db: Session, payload: RouteCreate) -> RouteDetailRead:
    normalized_origin = payload.origin.strip()
    normalized_destination = payload.destination.strip()
    _ensure_unique_route(
        db,
        origin=normalized_origin,
        destination=normalized_destination,
    )

    route = Route(
        origin=normalized_origin,
        destination=normalized_destination,
        distance_km=payload.distance_km,
        route_type=payload.route_type,
        price_20ft=payload.price_20ft,
        price_30ft=payload.price_30ft,
        price_40ft=payload.price_40ft,
        price_double=payload.price_double,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return RouteDetailRead.model_validate(route)


def update_route(
    db: Session,
    route_id: UUID,
    payload: RouteUpdate,
) -> RouteDetailRead:
    route = get_route(db, route_id)
    changes = payload.model_dump(exclude_unset=True)

    if "origin" in changes and changes["origin"] is not None:
        changes["origin"] = changes["origin"].strip()

    if "destination" in changes and changes["destination"] is not None:
        changes["destination"] = changes["destination"].strip()

    if "origin" in changes or "destination" in changes:
        _ensure_unique_route(
            db,
            origin=changes.get("origin", route.origin),
            destination=changes.get("destination", route.destination),
            exclude_route_id=route.id,
        )

    for field_name, value in changes.items():
        setattr(route, field_name, value)

    db.add(route)
    db.commit()
    db.refresh(route)
    return RouteDetailRead.model_validate(route)


def _ensure_unique_route(
    db: Session,
    origin: str,
    destination: str,
    exclude_route_id: Optional[UUID] = None,
) -> None:
    statement = select(Route).where(
        Route.origin == origin,
        Route.destination == destination,
    )
    if exclude_route_id is not None:
        statement = statement.where(Route.id != exclude_route_id)

    existing_route = db.scalar(statement)
    if existing_route is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A route with this origin and destination already exists.",
        )
