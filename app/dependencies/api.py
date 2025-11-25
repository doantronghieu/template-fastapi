"""API-layer dependencies for common request parameters."""

from fastapi import Query

from app.services.base_crud import PaginationType


class PaginationParams:
    """Reusable pagination parameters for list endpoints. All params are optional."""

    def __init__(
        self,
        limit: int | None = Query(None, ge=1, le=100, description="Max items per page"),
        offset: int | None = Query(None, ge=0, description="Number of items to skip"),
        cursor: str | None = Query(None, description="Cursor for cursor-based pagination"),
        pagination_type: PaginationType | None = Query(
            None, description="Pagination strategy: offset or cursor"
        ),
        order_by: str | None = Query(
            None, description="Order by field (prefix with - for DESC)"
        ),
    ):
        self.limit = limit
        self.offset = offset
        self.cursor = cursor
        self.pagination_type = pagination_type
        self.order_by = order_by
