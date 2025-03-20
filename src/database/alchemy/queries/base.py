from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Self, get_args, override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database._util import is_typevar
from src.database.alchemy import types
from src.database.alchemy.entity import Entity
from src.database.alchemy.tools import cursor_decoder, cursor_encoder, select_with_relations
from src.database.interfaces.query import Query


class ExtendedQuery[E: Entity, R](Query[AsyncSession, R]):
    _entity: type[E]
    __slots__ = (
        "_kw",
        "_entity",
    )

    def __init__(self, **kw: Any) -> None:
        self._kw = kw

    @property
    def entity(self) -> type[E]:
        if getattr(self, "_entity", None):
            return self._entity

        orig_bases = getattr(self, "__orig_bases__", None)

        assert orig_bases, "Generic type must be set"

        query, *_ = orig_bases

        entity, *_ = get_args(query)

        assert entity and not is_typevar(entity) and issubclass(entity, Entity), (
            "Generic first type must be a subclass of `Entity`"
        )

        self._entity = entity

        return self._entity

    @classmethod
    def with_(cls, entity: type[E]) -> type[Self]:
        return type(cls.__name__, (cls,), {"_entity": entity})


class Create[E: Entity](ExtendedQuery[E, E | None]):
    __slots__ = ()

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E | None:
        result = await conn.execute(
            insert(self.entity).on_conflict_do_nothing().values(**self._kw).returning(self.entity)
        )
        return result.scalars().first()


class BatchCreate[E: Entity](ExtendedQuery[E, Sequence[E]]):
    __slots__ = ("_data",)

    def __init__(self, data: Sequence[Mapping[str, Any]]) -> None:
        assert data, "data to create should not be empty"
        self._data = data

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.execute(
            insert(self.entity).on_conflict_do_nothing().returning(self.entity), self._data
        )

        return result.scalars().all()


class GetOne[E: Entity](ExtendedQuery[E, E | None]):
    __slots__ = (
        "_clauses",
        "_loads",
        "_lock",
    )

    def __init__(self, *_loads: str, lock_for_update: bool = False, **kw: Any) -> None:
        self._lock = lock_for_update
        self._loads = _loads
        self._clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E | None:
        stmt = select_with_relations(
            *self._loads,
            entity=self.entity,
            _node=kw.pop("_node", None),
            self_key=kw.pop("self_key", None),
            **kw,
        ).where(*self._clauses)

        if self._lock:
            stmt = stmt.with_for_update()

        return (await conn.scalars(stmt)).unique().first()


class GetManyByOffset[E: Entity](ExtendedQuery[E, types.OffsetPaginationResult[E]]):
    __slots__ = (
        "loads",
        "clauses",
        "limit",
        "offset",
        "order_by",
    )

    def __init__(
        self,
        *loads: str,
        order_by: types.OrderBy = "ASC",
        offset: int | None = None,
        limit: int | None = None,
        **kw: Any,
    ) -> None:
        self.loads = loads
        self.order_by = order_by.lower()
        self.offset = offset
        self.limit = limit
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> types.OffsetPaginationResult[E]:
        return await self._perform(conn, **kw)

    async def _perform(
        self,
        conn: AsyncSession,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> types.OffsetPaginationResult[E]:
        total = (await conn.execute(self._count_stmt(*clauses))).scalar() or 0

        if total <= 0:
            return types.OffsetPaginationResult[E](
                items=[], limit=self.limit, offset=self.offset, total=total
            )

        items = (await conn.scalars(self._items_stmt(*clauses, **kw))).unique().all()

        return types.OffsetPaginationResult[E](
            items=items,
            limit=self.limit,
            offset=self.offset,
            total=total,
        )

    def _items_stmt(
        self, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> sa.Select[tuple[E]]:
        return (
            select_with_relations(
                *self.loads,
                entity=self.entity,
                _node=kw.pop("_node", None),
                self_key=kw.pop("self_key", None),
                **kw,
            )
            .limit(self.limit)
            .offset(self.offset)
            .order_by(getattr(self.entity.id, self.order_by)())
            .where(*(self.clauses + list(clauses)))
        )

    def _count_stmt(self, *clauses: sa.ColumnExpressionArgument[bool]) -> sa.Select[tuple[int]]:
        return (
            sa.select(sa.func.count())
            .select_from(self.entity)
            .where(*(self.clauses + list(clauses)))
        )


class GetManyByCursor[E: Entity](ExtendedQuery[E, types.CursorPaginationResult[str, E]]):
    __slots__ = (
        "loads",
        "clauses",
        "limit",
        "order_by",
        "cursor",
        "cursor_type",
        "encoder",
        "decoder",
    )

    def __init__(
        self,
        *loads: str,
        order_by: types.OrderBy = "ASC",
        limit: int,
        cursor_type: types.CursorType,
        cursor: str | None = None,
        encoder: types.JsonDumps = json.dumps,
        decoder: types.JsonLoads = json.loads,
        **kw: Any,
    ) -> None:
        self.loads = loads
        self.order_by = order_by.lower()
        self.limit = limit
        self.cursor = cursor
        self.encoder = encoder
        self.decoder = decoder
        self.cursor_type = cursor_type.lower()
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(
        self, conn: AsyncSession, /, **kw: Any
    ) -> types.CursorPaginationResult[str, E]:
        if self.cursor_type == "integer":
            return await self._paginate_integer(conn, **kw)

        return await self._paginate_uuid(conn, **kw)

    async def _paginate_uuid(
        self, conn: AsyncSession, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> types.CursorPaginationResult[str, E]:
        assert hasattr(self.entity, "created_at"), (
            "To use UUID pagination you should have `created_at` field"
        )

        entity_created_at = self.entity.created_at  # type: ignore

        stmt = (
            select_with_relations(
                *self.loads,
                entity=self.entity,
                _node=kw.pop("_node", None),
                self_key=kw.pop("self_key", None),
                **kw,
            )
            .limit(self.limit)
            .order_by(
                getattr(entity_created_at, self.order_by)(),
                getattr(self.entity.id, self.order_by)(),
            )
        )
        if self.cursor:
            created_at, id = cursor_decoder(self.cursor, self.decoder, "UUID")
            if self.order_by == "asc":
                stmt = stmt.where(sa.tuple_(entity_created_at, self.entity.id) > (created_at, id))
            else:
                stmt = stmt.where(sa.tuple_(entity_created_at, self.entity.id) < (created_at, id))

        result = (await conn.scalars(stmt.where(*(self.clauses + list(clauses))))).unique().all()

        if result:
            last = result[-1]
            assert hasattr(last, "created_at"), (
                "To use UUID pagination you should have `created_at` field"
            )
            if len(result) < self.limit and self.limit > 1:
                next_cursor = ""
            else:
                next_cursor = cursor_encoder((last.created_at, last.id), self.encoder, "UUID")

            return types.CursorPaginationResult(
                items=result,
                results_per_page=self.limit,
                cursor=next_cursor,
            )

        return types.CursorPaginationResult(
            items=[],
            results_per_page=self.limit,
            cursor="",
        )

    async def _paginate_integer(
        self, conn: AsyncSession, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> types.CursorPaginationResult[str, E]:
        stmt = (
            select_with_relations(
                *self.loads,
                entity=self.entity,
                _node=kw.pop("_node", None),
                self_key=kw.pop("self_key", None),
                **kw,
            )
            .limit(self.limit)
            .order_by(
                getattr(self.entity.id, self.order_by)(),
            )
        )
        if self.cursor:
            decoded = cursor_decoder(self.cursor, self.decoder, "INTEGER")
            if self.order_by == "asc":
                stmt = stmt.where(self.entity.id > decoded)
            else:
                stmt = stmt.where(self.entity.id < decoded)

        result = (await conn.scalars(stmt.where(*(self.clauses + list(clauses))))).unique().all()

        if result:
            last = result[-1]
            if len(result) < self.limit and self.limit > 1:
                next_cursor = ""
            else:
                next_cursor = cursor_encoder(last.id, self.encoder, "INTEGER")

            return types.CursorPaginationResult(
                items=result,
                results_per_page=self.limit,
                cursor=next_cursor,
            )

        return types.CursorPaginationResult(
            items=[],
            results_per_page=self.limit,
            cursor="",
        )


class Update[E: Entity](ExtendedQuery[E, Sequence[E]]):
    __slots__ = ("clauses",)

    def __init__(self, data: Any, **filters: Any) -> None:
        assert data, "At least one field to update must be set"
        super().__init__(**data)
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in filters.items() if v is not None
        ]

    def filter(self, **kw: Any) -> Update[E]:
        self.clauses += [getattr(self.entity, k) == v for k, v in kw.items() if v is not None]

        return self

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.scalars(
            sa.update(self.entity).where(*self.clauses).values(**self._kw).returning(self.entity)
        )

        return result.unique().all()


class Delete[E: Entity](ExtendedQuery[E, Sequence[E]]):
    __slots__ = ("clauses",)

    def __init__(self, **kw: Any) -> None:
        assert kw, "At least one identifier must be provided"
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.execute(
            sa.delete(self.entity).where(*self.clauses).returning(self.entity)
        )

        return result.scalars().unique().all()


class Exists[E: Entity](ExtendedQuery[E, bool]):
    __slots__ = ("clauses",)

    def __init__(self, **kw: Any) -> None:
        assert kw, "At least one identifier must be provided"
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> bool:
        is_exist = await conn.execute(
            sa.exists(sa.select(self.entity.id).where(*self.clauses)).select()
        )

        return bool(is_exist.scalar())
