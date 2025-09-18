from typing import Unpack

import sqlalchemy as sa

from backend.app import dto
from backend.app.contracts import pagination
from backend.app.contracts.types.user import (
    CreateUserData,
    FilterManyUser,
    FilterOneUser,
    UpdateUserData,
)
from backend.infra.database.alchemy import entity, queries
from backend.infra.shared.result import as_result

from .base import BoundRepository


class UserRepositoryImpl(BoundRepository[entity.User]):
    @as_result()
    async def get_one(self, **filters: Unpack[FilterOneUser]) -> dto.user.UserPublic | None:
        result = await self._dao.get_one(for_update={}, **filters)

        return dto.user.UserPublic.from_attributes(result) if result else None

    @as_result()
    async def get_many_by_offset(
        self,
        offset: int,
        limit: int,
        order_by: pagination.SortOrder = "ASC",
        **filters: Unpack[FilterManyUser],
    ) -> pagination.OffsetPaginationResult[dto.user.UserPublic]:
        clauses: list[sa.ColumnExpressionArgument[bool]] = []
        if from_date := filters.pop("from_date", None):
            clauses.append(sa.cast(self._entity.created_at, sa.Date) >= from_date)

        if to_date := filters.pop("to_date", None):
            clauses.append(sa.cast(self._entity.created_at, sa.Date) <= to_date)

        query = queries.base.GetManyByOffset.with_(self._entity)(
            offset=offset, limit=limit, order_by=order_by, **filters
        )

        result = await self._manager.send(query.add_clauses(*clauses))

        return pagination.OffsetPaginationResult(
            items=[dto.user.UserPublic.from_attributes(item) for item in result.items],
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        )

    @as_result()
    async def create(self, data: CreateUserData) -> dto.user.UserPublic | None:
        result = await self._dao.create(**data.as_dict())

        return dto.user.UserPublic.from_attributes(result) if result else None

    @as_result()
    async def update(
        self, data: UpdateUserData, **filters: Unpack[FilterOneUser]
    ) -> dto.user.UserPublic | None:
        result = await self._dao.update(data.as_dict(), **filters)

        return dto.user.UserPublic.from_attributes(result[-1]) if result else None

    @as_result()
    async def delete(self, **filters: Unpack[FilterOneUser]) -> dto.user.UserPublic | None:
        result = await self._dao.delete(**filters)

        return dto.user.UserPublic.from_attributes(result[-1]) if result else None
