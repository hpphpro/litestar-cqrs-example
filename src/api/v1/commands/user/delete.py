import uuid
from dataclasses import dataclass
from typing import Any, override

from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.handler import Handler
from src.api.v1 import dto
from src.services.gateway import ServiceGateway


class DeleteUser(dto.BaseDTO):
    id: uuid.UUID


@dataclass(frozen=True, slots=True)
class DeleteUserHandler(Handler[Request[None, None, State], DeleteUser, None]):
    gateway: ServiceGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: DeleteUser, /, **kw: Any
    ) -> None:
        async with await self.gateway.manager.with_transaction():
            await self.gateway.user.delete(**qc.as_mapping())
