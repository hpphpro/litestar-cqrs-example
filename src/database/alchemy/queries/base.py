from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any, Final, Self, override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database._util import is_typevar
from src.database.alchemy import types
from src.database.alchemy.entity import Entity
from src.database.alchemy.tools import (
    cursor_decoder,
    cursor_encoder,
    get_entity_from_generic,
    select_with_relations,
)
from src.database.interfaces.query import Query


DEFAULT_CHUNK_LIMIT: Final[int] = 100
ALIAS_NAME: Final[str] = "selected_{name}"


class ExtendedQuery[E: Entity, R](Query[AsyncSession, R]):
    _entity: type[E]
    __slots__ = ("_kw",)

    def __init__(self, **kw: Any) -> None:
        self._kw = kw

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "_entity") or is_typevar(cls._entity):
            cls._entity = get_entity_from_generic(cls)

        return super().__init_subclass__()

    @property
    def entity(self) -> type[E]:
        entity: type[E] = self.__class__._entity

        assert not is_typevar(entity) and isinstance(entity, type) and issubclass(entity, Entity), (
            f"The class `{type(self)} has an unbound type variable for the entity. "
            "You need to specify a concrete entity type using the `with_` "
            "method or by defining a subclass with specific entity type."
        )

        return entity

    @classmethod
    def with_(cls, entity: type[E]) -> type[Self]:
        return type(
            cls.__name__,
            (cls,),
            {"_entity": entity, "__slots__": cls.__slots__},
        )


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
        if not self.loads or not self.limit:
            query = (
                select_with_relations(*self.loads, entity=self.entity, **kw)
                .limit(self.limit)
                .offset(self.offset)
                .order_by(getattr(self.entity.id, self.order_by)())
                .where(*(self.clauses + list(clauses)))
            )
        else:
            cte = (
                sa.select(self.entity.id)
                .limit(self.limit)
                .offset(self.offset)
                .order_by(getattr(self.entity.id, self.order_by)())
                .where(*(self.clauses + list(clauses)))
                .cte(name=ALIAS_NAME.format(name=self.entity.__tablename__))
            )

            query = (
                select_with_relations(*self.loads, entity=self.entity, **kw)
                .where(self.entity.id.in_(sa.select(cte.c.id)))
                .order_by(getattr(self.entity.id, self.order_by)())
            )

        return query

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
        cursor_type: types.CursorType | None = None,
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
        self.cursor_type = (
            cursor_type.lower()
            if cursor_type
            else ("uuid" if self.entity.id.type.python_type is uuid.UUID else "integer")
        )
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(
        self, conn: AsyncSession, /, **kw: Any
    ) -> types.CursorPaginationResult[str, E]:
        return await self._paginate(conn, **kw)

    async def _paginate(
        self, conn: AsyncSession, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> types.CursorPaginationResult[str, E]:
        if self.cursor:
            id = cursor_decoder(self.cursor, self.decoder, self.cursor_type)  # type: ignore[call-overload]
            if self.order_by == "asc":
                self.clauses.append(self.entity.id > id)
            else:
                self.clauses.append(self.entity.id < id)

        result = (await conn.scalars(self._stmt(*clauses, **kw))).unique().all()

        if result:
            last = result[-1]
            next_cursor = cursor_encoder(last.id, self.encoder, self.cursor_type)  # type: ignore[call-overload]

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

    def _stmt(self, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any) -> sa.Select[tuple[E]]:
        if not self.loads:
            query = (
                sa.select(self.entity)
                .limit(self.limit)
                .order_by(
                    getattr(self.entity.id, self.order_by)(),
                )
                .where(*(self.clauses + list(clauses)))
            )
        else:
            cte = (
                sa.select(self.entity.id)
                .limit(self.limit)
                .order_by(getattr(self.entity.id, self.order_by)())
                .where(*(self.clauses + list(clauses)))
                .cte(name=ALIAS_NAME.format(name=self.entity.__tablename__))
            )

            query = (
                select_with_relations(*self.loads, entity=self.entity, **kw)
                .where(self.entity.id.in_(sa.select(cte.c.id)))
                .order_by(getattr(self.entity.id, self.order_by)())
            )

        return query


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
        # assert kw, "At least one identifier must be provided"
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


class ExecuteFunc[R](Query[AsyncSession, R | None]):
    __slots__ = ("_func",)

    def __init__(self, func: sa.Function[R]) -> None:
        self._func = func

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> R | None:
        return (await conn.execute(self._func)).scalar()


class Count[E: Entity](ExtendedQuery[E, int]):
    __slots__ = ("clauses",)

    def __init__(self, **kw: Any) -> None:
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> int:
        return await self._get_total(conn, **kw)

    async def _get_total(
        self, conn: AsyncSession, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> int:
        result = await conn.execute(
            sa.select(sa.func.count())
            .select_from(self.entity)
            .where(*(self.clauses + list(clauses)))
        )

        return result.scalar() or 0


class IterChunked[E: Entity](ExtendedQuery[E, AsyncIterator[E]]):
    __slots__ = (
        "clauses",
        "chunk_limit",
        "loads",
        "order_by",
    )

    def __init__(
        self,
        *loads: str,
        chunk_limit: int = DEFAULT_CHUNK_LIMIT,
        order_by: types.OrderBy = "ASC",
        **kw: Any,
    ) -> None:
        self.order_by = order_by.lower()
        self.chunk_limit = chunk_limit
        self.loads = loads
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in kw.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> AsyncIterator[E]:
        return self._iter(conn, **kw)

    async def _iter(
        self, conn: AsyncSession, /, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any
    ) -> AsyncIterator[E]:
        result = await conn.stream(self._stmt(*clauses, **kw))

        async for chunk in result.unique().scalars().yield_per(self.chunk_limit):
            yield chunk

    def _stmt(self, *clauses: sa.ColumnExpressionArgument[bool], **kw: Any) -> sa.Select[tuple[E]]:
        return (
            select_with_relations(*self.loads, entity=self.entity, **kw)
            .order_by(getattr(self.entity.id, self.order_by)())
            .where(*(self.clauses + list(clauses)))
        )
