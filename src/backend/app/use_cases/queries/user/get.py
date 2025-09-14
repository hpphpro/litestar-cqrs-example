from dataclasses import dataclass
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.pagination import OffsetPagination
from backend.app.contracts.types.user import FilterManyUser, FilterOneUser


class GetOneUserQuery(dto.BaseDTO):
    filters: FilterOneUser


@dataclass(frozen=True, slots=True)
class GetOneUserQueryHandler(Handler[Context, GetOneUserQuery, dto.user.UserPublic]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GetOneUserQuery, /) -> dto.user.UserPublic:
        async with self.gateway.manager:
            result = await self.gateway.user.get_one(**qc.filters)

        return result.map(dto.user.UserPublic.from_attributes).unwrap_or_raise(
            exc.NotFoundError("User not found"),
        )


class GetManyOffsetUserQuery(dto.BaseDTO):
    pagination: OffsetPagination
    filters: FilterManyUser


@dataclass(frozen=True, slots=True)
class GetManyOffsetUserQueryHandler(
    Handler[Context, GetManyOffsetUserQuery, dto.OffsetResult[dto.user.UserPublic]],
):
    gateway: RepositoryGateway

    @override
    async def __call__(
        self,
        ctx: Context,
        qc: GetManyOffsetUserQuery,
        /,
    ) -> dto.OffsetResult[dto.user.UserPublic]:
        async with self.gateway.manager:
            result = await self.gateway.user.get_many_by_offset(
                **qc.pagination.as_dict(),
                **qc.filters,
            )

        return result.map(
            lambda r: dto.OffsetResult[dto.user.UserPublic].from_(r, dto.user.UserPublic)
        ).unwrap()
