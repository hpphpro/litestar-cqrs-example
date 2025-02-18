from dataclasses import dataclass
from typing import Annotated, Any, override

from litestar import Request
from litestar.datastructures import State
from msgspec import Meta

from src.api.common.interfaces.handler import Handler
from src.api.v1 import dto
from src.api.v1.commands.constants import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from src.services.gateway import ServiceGateway


class CreateUser(dto.BaseDTO):
    login: str
    password: Annotated[
        str,
        Meta(
            min_length=MIN_PASSWORD_LENGTH,
            max_length=MAX_PASSWORD_LENGTH,
            description=(
                f"Password between `{MIN_PASSWORD_LENGTH}` and "
                f"`{MAX_PASSWORD_LENGTH}` characters long"
            ),
        ),
    ]


@dataclass(frozen=True, slots=True)
class CreateUserHandler(Handler[Request[None, None, State], CreateUser, dto.user.User]):
    gateway: ServiceGateway

    @override
    async def __call__(
        self, request: Request[None, None, State], qc: CreateUser, /, **kw: Any
    ) -> dto.user.User:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.user.create(**qc.as_mapping())

        return dto.user.User.from_mapping(result.as_dict())
