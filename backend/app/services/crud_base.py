"""Generic async CRUD service with tenant scoping and q/skip/limit search."""
from typing import Any, Generic, TypeVar

from sqlalchemy import String, Text, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDService(Generic[ModelT]):
    """Reusable tenant-scoped CRUD operations for a single model."""

    def __init__(self, model: type[ModelT], search_fields: tuple[str, ...] = ("name",)) -> None:
        self.model = model
        self.search_fields = tuple(f for f in search_fields if hasattr(model, f))

    def _base_query(self, tenant_id: str):
        stmt = select(self.model)
        if hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        return stmt

    async def list(
        self,
        db: AsyncSession,
        *,
        tenant_id: str,
        q: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> list[ModelT]:
        """List rows for a tenant with optional case-insensitive search + filters."""
        stmt = self._base_query(tenant_id)
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        if q and self.search_fields:
            like = f"%{q}%"
            stmt = stmt.where(or_(*(getattr(self.model, f).ilike(like) for f in self.search_fields)))
        order_col = getattr(self.model, "created_at", None)
        if order_col is not None:
            stmt = stmt.order_by(order_col.desc())
        stmt = stmt.offset(max(skip, 0)).limit(max(1, min(limit, 200)))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, *, tenant_id: str, item_id: str) -> ModelT:
        """Fetch one row by id, tenant-scoped. Raises NotFoundError."""
        stmt = self._base_query(tenant_id).where(self.model.id == item_id)
        result = await db.execute(stmt)
        obj = result.scalars().first()
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} {item_id} not found")
        return obj

    async def create(self, db: AsyncSession, *, tenant_id: str, data: dict[str, Any]) -> ModelT:
        """Create a row, forcing tenant_id from the caller's token."""
        if hasattr(self.model, "tenant_id"):
            data = {**data, "tenant_id": tenant_id}
        obj = self.model(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, *, obj: ModelT, data: dict[str, Any]) -> ModelT:
        """Apply a partial update (ignores unknown/None-only semantics upstream)."""
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, *, obj: ModelT) -> None:
        """Delete a row."""
        await db.delete(obj)
        await db.commit()
