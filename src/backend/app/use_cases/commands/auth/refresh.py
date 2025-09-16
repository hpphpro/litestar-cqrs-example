from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import (
    Context,
    Fingerprint,
    JwtToken,
    RefreshStore,
    TokenPair,
)
from backend.app.use_cases.transform import handler


class RefreshUserCommand(dto.BaseDTO):
    data: dto.user.RefreshUser
    token: JwtToken


@handler
class RefreshUserCommandHandler(Handler[Context, RefreshUserCommand, TokenPair]):
    refresh_store: RefreshStore

    @override
    async def __call__(self, ctx: Context, qc: RefreshUserCommand, /) -> TokenPair:
        result = await self.refresh_store.rotate(Fingerprint(qc.data.fingerprint), qc.token)

        return result.unwrap_or_raise(exc.UnAuthorizedError("Token is invalid or expired"))
