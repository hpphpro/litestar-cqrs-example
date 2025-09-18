from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Mapping, Sequence
from functools import lru_cache
from types import GenericAlias
from typing import Any, Final, Self, override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.pagination import (
    CursorPaginationResult,
    OffsetPaginationResult,
    SortOrder,
)
from backend.app.contracts.query import Query
from backend.infra.database.alchemy import types
from backend.infra.database.alchemy.entity import Entity
from backend.infra.database.alchemy.tools import (
    cursor_decoder,
    cursor_encoder,
    get_entity_from_generic,
    get_primary_key,
    get_table_name,
    sqla_select,
)
from backend.shared.types import JsonDumps, JsonLoads, is_typevar


DEFAULT_CHUNK_LIMIT: Final[int] = 100
ALIAS_NAME: Final[str] = "selected_{name}"


@lru_cache
def _cached_query[E: Entity, T: ExtendedQuery[Any, Any]](cls: type[T], entity: type[E]) -> type[T]:
    return type(
        cls.__name__,
        (cls,),
        {"_entity": entity, "__slots__": cls.__slots__},
    )


class ExtendedQuery[E: Entity, R](Query[AsyncSession, R]):
    _entity: type[E]
    __slots__ = ("_kw",)

    def __init__(self, **kw: Any) -> None:
        self._kw = kw

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "_entity") or is_typevar(cls._entity):
            cls._entity = get_entity_from_generic(cls)

        return super().__init_subclass__()

    def __class_getitem__(cls, item: Any) -> Any:
        return cls.with_(item) if not isinstance(item, tuple) else GenericAlias(cls, item)

    @property
    def entity(self) -> type[E]:
        entity: type[E] = self._entity

        assert not is_typevar(entity) and isinstance(entity, type) and issubclass(entity, Entity), (  # noqa: PT018
            f"The class `{type(self)} has an unbound type variable for the entity. "
            "You need to specify a concrete entity type using the `with_` or `Cls[Concrete]` "
            "method or by defining a subclass with specific entity type."
        )

        return entity

    @classmethod
    def with_(cls, entity: type[E]) -> type[Self]:
        return _cached_query(cls, entity)


class ExtendedQueryWithFilters[E: Entity, R](ExtendedQuery[E, R]):
    __slots__ = ("clauses",)
    clauses: list[sa.ColumnExpressionArgument[bool]]

    def add_clauses(self, *clauses: sa.ColumnExpressionArgument[bool]) -> Self:
        self.clauses.extend(clauses)

        return self


class CreateOrIgnore[E: Entity](ExtendedQuery[E, E | None]):
    __slots__ = ()

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E | None:
        result = await conn.execute(
            insert(self.entity).on_conflict_do_nothing().values(**self._kw).returning(self.entity),
        )

        return result.scalars().first()


class Create[E: Entity](ExtendedQuery[E, E]):
    __slots__ = ()

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E:
        result = await conn.execute(
            insert(self.entity).values(**self._kw).returning(self.entity),
        )

        return result.scalars().one()


class CreateOrReplace[E: Entity](ExtendedQuery[E, E]):
    __slots__ = ()

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E:
        stmt = insert(self.entity).values(**self._kw)

        index_elements = [k.name for k in self.entity.__table__.primary_key]
        result = await conn.execute(
            stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_={k: getattr(stmt.excluded, k) for k in self._kw if k not in index_elements},
            ).returning(self.entity),
        )

        return result.scalars().one()


class BatchCreate[E: Entity](ExtendedQuery[E, Sequence[E]]):
    __slots__ = ("_data",)

    def __init__(self, data: Sequence[Mapping[str, Any]]) -> None:
        assert data, "data to create should not be empty"
        self._data = data

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.execute(
            insert(self.entity).on_conflict_do_nothing().returning(self.entity),
            self._data,
        )

        return result.scalars().all()


class GetOne[E: Entity](ExtendedQueryWithFilters[E, E | None]):
    __slots__ = (
        "_loads",
        "clauses",
        "for_update",
    )

    def __init__(
        self,
        *_loads: str,
        for_update: types.OnUpdateType | None = None,
        **eq_filters: Any,
    ) -> None:
        self._loads = _loads
        self.for_update = for_update
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> E | None:
        stmt = sqla_select(model=self.entity, loads=self._loads, **kw).where(*self.clauses)
        if self.for_update is not None:
            stmt = stmt.with_for_update(**({"of": self.entity} | self.for_update))

        return (await conn.scalars(stmt)).unique().first()


class GetAll[E: Entity](ExtendedQueryWithFilters[E, Sequence[E]]):
    __slots__ = ("_loads", "clauses")

    def __init__(self, *loads: str, **eq_filters: Any) -> None:
        self._loads = loads
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        stmt = sqla_select(model=self.entity, loads=self._loads, **kw).where(*self.clauses)

        return (await conn.scalars(stmt)).unique().all()


class GetManyByOffset[E: Entity](ExtendedQueryWithFilters[E, OffsetPaginationResult[E]]):
    __slots__ = (
        "_loads",
        "clauses",
        "for_update",
        "limit",
        "offset",
        "order_by",
    )

    def __init__(
        self,
        *loads: str,
        order_by: SortOrder = "ASC",
        offset: int | None = None,
        limit: int | None = None,
        for_update: types.OnUpdateType | None = None,
        **eq_filters: Any,
    ) -> None:
        self._loads = loads
        self.for_update = for_update
        self.order_by = order_by.lower()
        self.offset = offset
        self.limit = limit
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> OffsetPaginationResult[E]:
        return await self.perform(conn, **kw)

    async def perform(
        self,
        conn: AsyncSession,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> OffsetPaginationResult[E]:
        params = kw.pop("params", None)
        total = (await conn.execute(self.make_count_stmt(*clauses), params)).scalar() or 0

        if total <= 0:
            return OffsetPaginationResult[E](
                items=[],
                limit=self.limit,
                offset=self.offset,
                total=total,
            )

        stmt = self.make_items_stmt(*clauses, **kw)
        if self.for_update is not None:
            stmt = stmt.with_for_update(**({"of": self.entity} | self.for_update))

        items = (await conn.scalars(stmt, params)).unique().all()

        return OffsetPaginationResult[E](
            items=items,
            limit=self.limit,
            offset=self.offset,
            total=total,
        )

    def make_items_stmt(
        self,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> sa.Select[tuple[E]]:
        base_select = sqla_select(model=self.entity, loads=self._loads, **kw)
        pk = get_primary_key(self.entity)
        if not self._loads or not self.limit:
            self.add_clauses(*clauses)

            query = (
                base_select.limit(self.limit)
                .offset(self.offset)
                .order_by(getattr(pk, self.order_by)())
                .where(*self.clauses)
            )
        else:
            cte = (
                sa.select(pk)
                .limit(self.limit)
                .offset(self.offset)
                .order_by(getattr(pk, self.order_by)())
                .where(*self.clauses)
                .cte(name=ALIAS_NAME.format(name=get_table_name(self.entity)))
            )

            query = (
                base_select.join(cte, pk == getattr(cte.c, pk.name))
                .order_by(getattr(pk, self.order_by)())
                .where(*clauses)
            )

        return query

    def make_count_stmt(self, *clauses: sa.ColumnExpressionArgument[bool]) -> sa.Select[tuple[int]]:
        return (
            sa.select(sa.func.count())
            .select_from(self.entity)
            .where(*(self.clauses + list(clauses)))
        )


class GetManyByCursor[E: Entity](ExtendedQueryWithFilters[E, CursorPaginationResult[str, E]]):
    __slots__ = (
        "_loads",
        "clauses",
        "cursor",
        "cursor_type",
        "decoder",
        "encoder",
        "for_update",
        "limit",
        "order_by",
    )

    def __init__(
        self,
        *loads: str,
        order_by: SortOrder = "ASC",
        limit: int,
        cursor_type: types.CursorType | None = None,
        cursor: str | None = None,
        for_update: types.OnUpdateType | None = None,
        encoder: JsonDumps = json.dumps,
        decoder: JsonLoads = json.loads,
        **eq_filters: Any,
    ) -> None:
        self._loads = loads
        self.order_by = order_by.lower()
        self.limit = limit
        self.cursor = cursor
        self.encoder = encoder
        self.decoder = decoder
        self.for_update = for_update
        self.cursor_type: types.CursorType = (
            cursor_type
            if cursor_type
            else (
                "uuid" if get_primary_key(self.entity).type.python_type is uuid.UUID else "integer"
            )
        )
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> CursorPaginationResult[str, E]:
        return await self.perform(conn, **kw)

    async def perform(
        self,
        conn: AsyncSession,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> CursorPaginationResult[str, E]:
        pk = get_primary_key(self.entity)
        if self.cursor:
            id_ = cursor_decoder(self.cursor, self.decoder, self.cursor_type)

            self.clauses.append(pk > id_ if self.order_by == "asc" else pk < id_)

        stmt = self.make_stmt(*clauses, **kw)
        if self.for_update is not None:
            stmt = stmt.with_for_update(**({"of": self.entity} | self.for_update))

        result = (await conn.scalars(stmt, params=kw.pop("params", None))).unique().all()

        items = result[: self.limit]
        if len(result) > self.limit:
            last = items[-1]
            next_cursor = cursor_encoder(getattr(last, pk.name), self.encoder, self.cursor_type)
        else:
            next_cursor = ""

        return CursorPaginationResult(
            items=items,
            results_per_page=len(items),
            cursor=next_cursor,
        )

    def make_stmt(
        self,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> sa.Select[tuple[E]]:
        limit = self.limit + 1
        pk = get_primary_key(self.entity)
        if not self._loads:
            self.add_clauses(*clauses)

            query = (
                sa.select(self.entity)
                .limit(limit)
                .order_by(getattr(pk, self.order_by)())
                .where(*self.clauses)
            )
        else:
            cte = (
                sa.select(pk)
                .limit(limit)
                .order_by(getattr(pk, self.order_by)())
                .where(*self.clauses)
                .cte(name=ALIAS_NAME.format(name=get_table_name(self.entity)))
            )

            query = (
                sqla_select(model=self.entity, loads=self._loads, **kw)
                .join(cte, pk == getattr(cte.c, pk.name))
                .order_by(getattr(pk, self.order_by)())
                .where(*clauses)
            )

        return query


class Update[E: Entity](ExtendedQueryWithFilters[E, Sequence[E]]):
    __slots__ = ("clauses",)

    def __init__(self, data: Any, **eq_filters: Any) -> None:
        assert data, "At least one field to update must be set"
        super().__init__(**data)
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.scalars(
            sa.update(self.entity).where(*self.clauses).values(**self._kw).returning(self.entity),
        )

        return result.unique().all()


class Delete[E: Entity](ExtendedQueryWithFilters[E, Sequence[E]]):
    __slots__ = ("clauses",)

    def __init__(self, **eq_filters: Any) -> None:
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> Sequence[E]:
        result = await conn.scalars(
            sa.delete(self.entity).where(*self.clauses).returning(self.entity),
        )

        return result.unique().all()


class Exists[E: Entity](ExtendedQueryWithFilters[E, bool]):
    __slots__ = ("clauses",)

    def __init__(self, **eq_filters: Any) -> None:
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> bool:
        is_exist = await conn.execute(
            sa.exists(sa.select(sa.text("1")).where(*self.clauses)).select(),
        )

        return bool(is_exist.scalar())


class ExecuteFunc[R](Query[AsyncSession, R | None]):
    __slots__ = ("_func",)

    def __init__(self, func: sa.Function[R]) -> None:
        self._func = func

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> R | None:
        return (await conn.execute(sa.select(self._func))).scalar()


class Count[E: Entity](ExtendedQueryWithFilters[E, int]):
    __slots__ = ("clauses",)

    def __init__(self, **eq_filters: Any) -> None:
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> int:
        return await self.perform(conn, **kw)

    async def perform(
        self,
        conn: AsyncSession,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> int:
        self.add_clauses(*clauses)

        result = await conn.execute(
            sa.select(sa.func.count()).select_from(self.entity).where(*self.clauses),
        )

        return result.scalar() or 0


class IterChunked[E: Entity](ExtendedQueryWithFilters[E, AsyncIterator[E]]):
    __slots__ = (
        "_loads",
        "chunk_limit",
        "clauses",
        "order_by",
    )

    def __init__(
        self,
        *loads: str,
        chunk_limit: int = DEFAULT_CHUNK_LIMIT,
        order_by: SortOrder = "ASC",
        **eq_filters: Any,
    ) -> None:
        self._loads = loads
        self.order_by = order_by.lower()
        self.chunk_limit = chunk_limit
        self.clauses: list[sa.ColumnExpressionArgument[bool]] = [
            getattr(self.entity, k) == v for k, v in eq_filters.items() if v is not None
        ]

    @override
    async def __call__(self, conn: AsyncSession, /, **kw: Any) -> AsyncIterator[E]:
        return self._iter(conn, **kw)

    async def _iter(
        self,
        conn: AsyncSession,
        /,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> AsyncIterator[E]:
        result = await conn.stream(self.make_stmt(*clauses, **kw))

        async for chunk in result.unique().scalars().yield_per(self.chunk_limit):
            yield chunk

    def make_stmt(
        self,
        *clauses: sa.ColumnExpressionArgument[bool],
        **kw: Any,
    ) -> sa.Select[tuple[E]]:
        pk = get_primary_key(self.entity)
        self.add_clauses(*clauses)

        return (
            sqla_select(model=self.entity, loads=self._loads, **kw)
            .order_by(getattr(pk, self.order_by)())
            .where(*self.clauses)
        )
