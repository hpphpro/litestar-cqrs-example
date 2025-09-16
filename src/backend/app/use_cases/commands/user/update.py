from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context, Hasher
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types.user import FilterOneUser, UpdateUserData
from backend.app.use_cases.transform import handler


class UpdateUserCommand(dto.BaseDTO):
    filters: FilterOneUser
    data: UpdateUserData


@handler
class UpdateUserCommandHandler(Handler[Context, UpdateUserCommand, dto.Status]):
    gateway: RepositoryGateway
    hasher: Hasher

    @override
    async def __call__(self, ctx: Context, qc: UpdateUserCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            if qc.data.password is not None:
                qc.data.password = self.hasher.hash_password(qc.data.password).unwrap()

            result = await self.gateway.user.update(qc.data, **qc.filters)

            result.map_err(exc.ConflictError.from_other).unwrap()

        return dto.Status(status=result.is_ok())
