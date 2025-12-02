"""Generic base CRUD service for common database operations."""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any, Generic, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=SQLModel)

FILTER_OPERATORS = {
    "__eq": lambda col, val: col == val,
    "__ne": lambda col, val: col != val,
    "__gt": lambda col, val: col > val,
    "__gte": lambda col, val: col >= val,
    "__lt": lambda col, val: col < val,
    "__lte": lambda col, val: col <= val,
    "__in": lambda col, val: col.in_(val),
    "__like": lambda col, val: col.like(val),
    "__ilike": lambda col, val: col.ilike(val),
}


class PaginationType(str, Enum):
    """Pagination strategy type."""

    OFFSET = "offset"
    CURSOR = "cursor"


class PaginatedResponse(BaseModel):
    """Generic paginated response container."""

    items: list[Any]
    total: int | None = None
    cursor: str | None = None
    has_more: bool = False


class BaseCRUDService(Generic[ModelType]):
    """
    Generic base CRUD service providing standard database operations.

    Type-safe generic operations for any SQLModel with auto-commit,
    soft delete detection, and comprehensive querying capabilities.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        self._has_soft_delete = hasattr(model, "deleted_at")

    def _filter_soft_deleted(self, query: Select) -> Select:
        """Apply soft delete filter if model supports it."""
        if self._has_soft_delete:
            return query.where(self.model.deleted_at.is_(None))
        return query

    def _to_dict(self, obj_in: BaseModel | dict[str, Any]) -> dict[str, Any]:
        """Convert Pydantic model to dict if needed."""
        if isinstance(obj_in, BaseModel):
            return obj_in.model_dump(exclude_unset=True)
        return obj_in

    async def _commit_and_refresh(self, instance: ModelType) -> ModelType:
        """Commit transaction and refresh instance."""
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    def _validate_field(self, field: str) -> bool:
        """Validate field exists on model. Logs warning if not found."""
        if not hasattr(self.model, field):
            logger.warning(f"Field {field} not found on {self.model.__name__}")
            return False
        return True

    def _update_timestamp(self, instance: ModelType) -> None:
        """Update instance's updated_at timestamp if field exists."""
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(UTC)

    async def get_by_id(self, id: Any) -> ModelType:
        """Get single record by primary key. Raises 404 if not found."""
        query = select(self.model).where(self.model.id == id)
        query = self._filter_soft_deleted(query)

        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found",
            )

        return instance

    async def get_all(
        self,
        order_by: Annotated[
            str | list[str] | None,
            "Column(s) to order by. Prefix with '-' for DESC (e.g., '-created_at')",
        ] = None,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """Get all records with flexible ordering."""
        query = select(self.model)

        if not include_deleted:
            query = self._filter_soft_deleted(query)

        if order_by:
            query = self._apply_ordering(query, order_by)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_multi(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        cursor: Annotated[str | None, "Cursor value (ID) for keyset pagination"] = None,
        pagination_type: Annotated[
            PaginationType, "OFFSET for limit/offset, CURSOR for keyset pagination"
        ] = PaginationType.OFFSET,
        order_by: Annotated[
            str | list[str] | None,
            "Column(s) to order by. Prefix with '-' for DESC (e.g., '-created_at')",
        ] = None,
        filters: Annotated[
            dict[str, Any] | None,
            "Field filters with operators (e.g., {'email__ilike': '%@example.com', 'age__gt': 18})",
        ] = None,
        include_deleted: bool = False,
    ) -> PaginatedResponse:
        """Get paginated records with dual pagination strategies and advanced filtering."""
        query = select(self.model)

        if filters:
            query = self._apply_filters(query, filters)

        if not include_deleted:
            query = self._filter_soft_deleted(query)

        if pagination_type == PaginationType.CURSOR and cursor:
            query = query.where(self.model.id > cursor)
        elif pagination_type == PaginationType.OFFSET:
            query = query.offset(offset)

        if order_by:
            query = self._apply_ordering(query, order_by)

        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        response = PaginatedResponse(items=items, has_more=has_more)

        if pagination_type == PaginationType.CURSOR and items:
            response.cursor = str(items[-1].id)

        return response

    async def get_by_field(
        self,
        filters: Annotated[
            dict[str, Any],
            "Field filters with operators (e.g., {'email': 'user@example.com'}, {'age__gt': 18})",
        ],
        include_deleted: bool = False,
    ) -> ModelType | None:
        """Get single record by field(s) with operator support. Returns None if not found."""
        query = select(self.model)
        query = self._apply_filters(query, filters)

        if not include_deleted:
            query = self._filter_soft_deleted(query)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        obj_in: Annotated[
            BaseModel | dict[str, Any], "Pydantic model or dict with field values"
        ],
    ) -> ModelType:
        """Create new record with auto-commit and refresh."""
        data = self._to_dict(obj_in)
        instance = self.model(**data)
        self.session.add(instance)
        await self._commit_and_refresh(instance)

        logger.info(f"Created {self.model.__name__} with id {instance.id}")
        return instance

    async def update(
        self,
        id: Any,
        obj_in: Annotated[
            BaseModel | dict[str, Any], "Pydantic model or dict with fields to update"
        ],
    ) -> ModelType:
        """Update existing record with partial update (PATCH semantics). Raises 404 if not found."""
        instance = await self.get_by_id(id)
        data = self._to_dict(obj_in)

        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        self._update_timestamp(instance)
        await self._commit_and_refresh(instance)

        logger.info(f"Updated {self.model.__name__} with id {id}")
        return instance

    async def delete(self, id: Any) -> bool:
        """
        Smart delete - soft delete if model has 'deleted_at' field, otherwise hard delete.
        Raises 404 if not found.
        """
        instance = await self.get_by_id(id)

        if self._has_soft_delete:
            instance.deleted_at = datetime.now(UTC)
            self._update_timestamp(instance)
            logger.info(f"Soft deleted {self.model.__name__} with id {id}")
        else:
            await self.session.delete(instance)
            logger.info(f"Hard deleted {self.model.__name__} with id {id}")

        await self.session.commit()
        return True

    async def create_many(
        self,
        objs_in: Annotated[
            list[BaseModel | dict[str, Any]],
            "List of Pydantic models or dicts with field values",
        ],
    ) -> list[ModelType]:
        """Bulk create multiple records in single transaction."""
        instances = [self.model(**self._to_dict(obj_in)) for obj_in in objs_in]

        self.session.add_all(instances)
        await self.session.commit()

        for instance in instances:
            await self.session.refresh(instance)

        logger.info(f"Created {len(instances)} {self.model.__name__} records")
        return instances

    async def delete_many(self, ids: list[Any]) -> int:
        """Bulk delete multiple records. Returns count of successfully deleted records."""
        count = 0
        for id in ids:
            try:
                await self.delete(id)
                count += 1
            except HTTPException:
                pass

        logger.info(f"Deleted {count}/{len(ids)} {self.model.__name__} records")
        return count

    def _apply_filters(self, query: Select, filters: dict[str, Any]) -> Select:
        """
        Apply dynamic filters with operator support.
        Operators: __eq, __ne, __gt, __gte, __lt, __lte, __in, __like, __ilike.
        """
        for field_with_op, value in filters.items():
            if "__" in field_with_op:
                field, op = field_with_op.rsplit("__", 1)
                op = f"__{op}"
            else:
                field, op = field_with_op, "__eq"

            if not self._validate_field(field):
                continue

            column = getattr(self.model, field)

            if op in FILTER_OPERATORS:
                query = query.where(FILTER_OPERATORS[op](column, value))
            else:
                logger.warning(f"Unknown operator {op}")

        return query

    def _apply_ordering(self, query: Select, order_by: str | list[str]) -> Select:
        """Apply ordering to query. Prefix field with '-' for DESC."""
        if isinstance(order_by, str):
            order_by = [order_by]

        for order_field in order_by:
            if order_field.startswith("-"):
                field = order_field[1:]
                direction = desc
            else:
                field = order_field
                direction = asc

            if not self._validate_field(field):
                continue

            column = getattr(self.model, field)
            query = query.order_by(direction(column))

        return query
