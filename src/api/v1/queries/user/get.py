import uuid
from dataclasses import asdict, dataclass
from typing import Any, override

from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.handler import Handler
from src.api.v1 import dto
from src.database.alchemy.types import OrderBy
from src.services.gateway import ServiceGateway


class GetOneUser(dto.BaseDTO):
    id: uuid.UUID


@dataclass(frozen=True, slots=True)
class GetOneUserHandler(Handler[Request[None, None, State], GetOneUser, dto.user.User]):
    gateway: ServiceGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: GetOneUser, /, **kw: Any
    ) -> dto.user.User:
        async with self.gateway.manager:
            result = await self.gateway.user.get_one(**qc.as_mapping())

        return dto.user.User.from_mapping(result.as_dict())


class GetManyOffsetUser(dto.BaseDTO):
    offset: int
    limit: int
    order_by: OrderBy = "ASC"


@dataclass(frozen=True, slots=True)
class GetManyOffsetUserHandler(
    Handler[Request[None, None, State], GetManyOffsetUser, dto.OffsetResult[dto.user.User]]
):
    gateway: ServiceGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: GetManyOffsetUser, /, **kw: Any
    ) -> dto.OffsetResult[dto.user.User]:
        async with self.gateway.manager:
            result = await self.gateway.user.get_many_by_offset(**qc.as_mapping())

        return dto.OffsetResult[dto.user.User].from_mapping(asdict(result))
