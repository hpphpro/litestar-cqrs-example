from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types.user import FilterOneUser
from backend.app.use_cases.transform import handler


class DeleteUserCommand(dto.BaseDTO):
    filters: FilterOneUser


@handler
class DeleteUserCommandHandler(Handler[Context, DeleteUserCommand, None]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: DeleteUserCommand, /) -> None:
        async with await self.gateway.manager.with_transaction():
            (await self.gateway.user.delete(**qc.filters)).map_err(
                exc.NotFoundError.from_other
            ).unwrap()
