from dataclasses import dataclass
from typing import Any, override

import msgspec
from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.handler import Handler
from src.api.v1 import dto
from src.services.gateway import ServiceGateway


class UpdateUser(dto.BaseDTO):
    login: str | msgspec.UnsetType = msgspec.UNSET
    password: str | msgspec.UnsetType = msgspec.UNSET


@dataclass(frozen=True, slots=True)
class UpdateUserHandler(Handler[Request[None, None, State], UpdateUser, dto.Status]):
    gateway: ServiceGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: UpdateUser, /, **kw: Any
    ) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.user.update(**{**qc.as_mapping(), **kw})

        return dto.Status(status=bool(result))
