from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


def paginate(page: int, page_size: int, max_page_size: int) -> PaginationParams:
    normalized_page_size = min(max(page_size, 1), max_page_size)
    normalized_page = max(page, 1)

    return PaginationParams(
        page=normalized_page,
        page_size=normalized_page_size,
        skip=(normalized_page - 1) * normalized_page_size,
        limit=normalized_page_size,
    )


def build_paginated_response(
    items: list[T],
    total: int,
    pagination: PaginationParams,
) -> PaginatedResponse[T]:
    total_pages = ceil(total / pagination.page_size) if total else 0
    return PaginatedResponse(
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
        total_pages=total_pages,
    )
