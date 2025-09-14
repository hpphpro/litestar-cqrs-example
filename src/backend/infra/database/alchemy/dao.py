from __future__ import annotations

from collections.abc import Sequence
from typing import Any, overload

from backend.app.contracts.manager import TransactionManager
from backend.app.contracts.pagination import (
    CursorPaginationResult,
    OffsetPaginationResult,
    SortOrder,
)
from backend.infra.database.alchemy.entity import Entity

from . import types
from .queries import base


class DAO[E: Entity]:
    __slots__ = (
        "_entity",
        "_manager",
    )

    def __init__(self, manager: TransactionManager, entity: type[E]) -> None:
        self._manager = manager
        self._entity = entity

    async def create(self, **data: Any) -> E | None:
        return await self._manager.send(base.CreateOrIgnore.with_(self._entity)(**data))

    async def batch_create(self, data: list[Any]) -> Sequence[E]:
        return await self._manager.send(base.BatchCreate.with_(self._entity)(data))

    async def get_one(
        self,
        *loads: str,
        **data: Any,
    ) -> E | None:
        return await self._manager.send(base.GetOne.with_(self._entity)(*loads, **data))

    @overload
    async def get_many(
        self,
        *loads: str,
        limit: int,
        offset: int,
        order_by: SortOrder = "ASC",
        **filters: Any,
    ) -> OffsetPaginationResult[E]: ...
    @overload
    async def get_many(
        self,
        *loads: str,
        limit: int,
        order_by: SortOrder = "ASC",
        cursor: str | None,
        **filters: Any,
    ) -> CursorPaginationResult[str, E]: ...
    async def get_many(
        self,
        *loads: str,
        limit: int,
        order_by: SortOrder = "ASC",
        offset: int | types.UnsetType = types.UnsetType.UNSET,
        cursor: str | None | types.UnsetType = types.UnsetType.UNSET,
        **filters: Any,
    ) -> OffsetPaginationResult[E] | CursorPaginationResult[str, E]:
        result: OffsetPaginationResult[E] | CursorPaginationResult[str, E]

        if offset != types.UnsetType.UNSET:
            result = await self._manager.send(
                base.GetManyByOffset.with_(self._entity)(
                    *loads, order_by=order_by, offset=offset, limit=limit, **filters
                )
            )
        elif cursor != types.UnsetType.UNSET:
            result = await self._manager.send(
                base.GetManyByCursor.with_(self._entity)(
                    *loads, order_by=order_by, cursor=cursor, limit=limit, **filters
                )
            )
        else:
            raise RuntimeError("Invalid query param")

        return result

    async def update(self, data: Any, **filters: Any) -> Sequence[E]:
        return await self._manager.send(base.Update.with_(self._entity)(data, **filters))

    async def delete(self, **filters: Any) -> Sequence[E]:
        return await self._manager.send(base.Delete.with_(self._entity)(**filters))

    async def exists(self, **filters: Any) -> bool:
        return await self._manager.send(base.Exists.with_(self._entity)(**filters))

    def with_other[O: Entity](self, entity: type[O]) -> DAO[O]:
        return DAO[O](self._manager, entity)
