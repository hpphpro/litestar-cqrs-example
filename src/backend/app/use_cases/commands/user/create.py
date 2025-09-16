import uuid
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context, Hasher
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types.user import CreateUserData
from backend.app.use_cases.transform import handler


class CreateUserCommand(dto.BaseDTO):
    data: CreateUserData


@handler
class CreateUserCommandHandler(Handler[Context, CreateUserCommand, dto.Id[uuid.UUID]]):
    gateway: RepositoryGateway
    hasher: Hasher

    @override
    async def __call__(self, ctx: Context, qc: CreateUserCommand, /) -> dto.Id[uuid.UUID]:
        async with await self.gateway.manager.with_transaction():
            qc.data.password = self.hasher.hash_password(qc.data.password).unwrap()
            result = await self.gateway.user.create(qc.data)

        return dto.Id(
            id=result.unwrap_or_raise(exc.ConflictError("Conflict", detail="User not created")).id,
        )
