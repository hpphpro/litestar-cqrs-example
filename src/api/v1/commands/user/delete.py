import uuid
from dataclasses import dataclass
from typing import Any, override

from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.handler import Handler
from src.api.v1 import dto
from src.services.internal.interfaces import InternalGateway


class DeleteUser(dto.BaseDTO):
    id: uuid.UUID


@dataclass(frozen=True, slots=True)
class DeleteUserHandler(Handler[Request[None, None, State], DeleteUser, None]):
    gateway: InternalGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: DeleteUser, /, **kw: Any
    ) -> None:
        async with await self.gateway.manager.with_transaction():
            await self.gateway.user.delete(**qc.as_mapping())
