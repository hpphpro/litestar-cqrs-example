from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts.auth import (
    Context,
    Fingerprint,
    JwtToken,
    RefreshStore,
)
from backend.app.use_cases.transform import handler


class LogoutUserCommand(dto.BaseDTO):
    data: dto.user.LogoutUser
    token: JwtToken


@handler
class LogoutUserCommandHandler(Handler[Context, LogoutUserCommand, dto.Status]):
    refresh_store: RefreshStore

    @override
    async def __call__(self, ctx: Context, qc: LogoutUserCommand, /) -> dto.Status:
        result = await self.refresh_store.revoke(Fingerprint(qc.data.fingerprint), qc.token)

        return dto.Status(result.unwrap_or(default=False))
