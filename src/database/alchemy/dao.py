from collections.abc import Sequence
from typing import Any, overload

from src.database.alchemy import types
from src.database.alchemy.entity.base.core import Entity
from src.database.alchemy.queries import base
from src.database.interfaces.manager import TransactionManager


class DAO[E: Entity]:
    __slots__ = (
        "_manager",
        "_entity",
    )

    def __init__(self, manager: TransactionManager, entity: type[E]) -> None:
        self._manager = manager
        self._entity = entity

    async def create(self, **data: Any) -> E | None:
        return await self._manager.send(base.Create[E].with_(self._entity)(**data))

    async def batch_create(self, data: list[Any]) -> Sequence[E]:
        return await self._manager.send(base.BatchCreate[E].with_(self._entity)(data))

    async def get_one(
        self,
        *loads: str,
        **data: Any,
    ) -> E | None:
        return await self._manager.send(base.GetOne[E].with_(self._entity)(*loads, **data))

    @overload
    async def get_many(
        self,
        *loads: str,
        order_by: types.OrderBy = "ASC",
        limit: int,
        offset: int | None = None,
        **filters: Any,
    ) -> types.OffsetPaginationResult[E]: ...
    @overload
    async def get_many(
        self,
        *loads: str,
        order_by: types.OrderBy = "ASC",
        limit: int,
        cursor: str | None = None,
        **filters: Any,
    ) -> types.CursorPaginationResult[str, E]: ...
    async def get_many(
        self,
        *loads: str,
        order_by: types.OrderBy = "ASC",
        limit: int,
        offset: int | None = None,
        cursor: str | None = None,
        **filters: Any,
    ) -> types.OffsetPaginationResult[E] | types.CursorPaginationResult[str, E]:
        result: types.OffsetPaginationResult[E] | types.CursorPaginationResult[str, E]

        if offset is not None:
            result = await self._manager.send(
                base.GetManyByOffset[E].with_(self._entity)(
                    *loads, order_by=order_by, offset=offset, limit=limit, **filters
                )
            )
        elif cursor is not None:
            result = await self._manager.send(
                base.GetManyByCursor[E].with_(self._entity)(
                    *loads, order_by=order_by, cursor=cursor, limit=limit, **filters
                )
            )
        else:
            raise RuntimeError("Invalid query param")

        return result

    async def update(self, data: Any, **filters: Any) -> Sequence[E]:
        return await self._manager.send(base.Update[E].with_(self._entity)(data, **filters))

    async def delete(self, **filters: Any) -> Sequence[E]:
        return await self._manager.send(base.Delete[E].with_(self._entity)(**filters))

    async def exists(self, **filters: Any) -> bool:
        return await self._manager.send(base.Exists[E].with_(self._entity)(**filters))
