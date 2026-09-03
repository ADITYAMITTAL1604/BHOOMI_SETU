"""Pagination helper utilities — SQLAlchemy 2.0 compatible."""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PageResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def paginate(
    stmt,
    page: int = 1,
    page_size: int = 20,
    db: Optional[Session] = None,
) -> tuple[list, int]:
    """Apply pagination to a SQLAlchemy 2.0 Select statement.

    If *db* is provided, executes against that session and returns ORM objects.
    Legacy callers that pass an ORM Query object (without db) still work via
    the fallback branch.
    """
    if db is not None:
        # SQLAlchemy 2.0 path: stmt is a Select
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0
        items = db.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()
        return list(items), total
    else:
        # Legacy ORM Query fallback (should not normally be reached)
        total = stmt.with_entities(func.count()).scalar() or 0
        items = stmt.offset((page - 1) * page_size).limit(page_size).all()
        return items, total


def create_page_response(
    items: list[T],
    total: int,
    page: int,
    page_size: int,
) -> "PageResponse[T]":
    """Create a PageResponse from items and pagination info."""
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


def apply_pagination(
    stmt,
    page: int = 1,
    page_size: int = 20,
):
    """Apply LIMIT/OFFSET to a select statement."""
    return stmt.offset((page - 1) * page_size).limit(page_size)


def get_total_count(db: Session, stmt) -> int:
    """Get total count for a select statement."""
    count_stmt = select(func.count()).select_from(stmt.subquery())
    return db.execute(count_stmt).scalar() or 0