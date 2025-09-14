from dataclasses import dataclass
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import (
    Authenticator,
    Context,
    Fingerprint,
    Hasher,
    RefreshStore,
    TokenPair,
)
from backend.app.contracts.cache import StrCache
from backend.app.contracts.gateway import RepositoryGateway


class LoginUserCommand(dto.BaseDTO):
    data: dto.user.LoginUser


@dataclass(frozen=True, slots=True)
class LoginUserCommandHandler(Handler[Context, LoginUserCommand, TokenPair]):
    gateway: RepositoryGateway
    authenticator: Authenticator
    refresh_store: RefreshStore
    cache: StrCache
    hasher: Hasher

    @override
    async def __call__(self, ctx: Context, qc: LoginUserCommand, /) -> TokenPair:
        async with self.gateway.manager as manager:
            result = await self.authenticator.authenticate(manager, email=qc.data.email)

        user_id = result.and_then(
            lambda u: u
            if u.password and self.hasher.verify_password(u.password, qc.data.password).unwrap()
            else None
        ).unwrap_or_raise(exc.UnAuthorizedError("Invalid credentials"))

        return (
            (await self.refresh_store.make_token(user_id.id, Fingerprint(qc.data.fingerprint)))
            .map_err(exc.ServiceNotImplementedError.from_other)
            .unwrap()
        )
