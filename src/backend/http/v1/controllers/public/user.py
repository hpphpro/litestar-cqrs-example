import uuid
from typing import Annotated

from litestar import Controller, MediaType, Request, post, status_codes
from litestar.datastructures import State
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.params import Body

from backend.app import dto
from backend.app.contracts.types.user import (
    CreateUserData,
)
from backend.app.use_cases import commands
from backend.http.common import docs


class UserController(Controller):
    path = "/users"
    tags = ["user"]

    @post(
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.Conflict.to_spec()
        | docs.InternalServer.to_spec()
        | docs.TooManyRequests.to_spec(),
        middleware=[RateLimitConfig(("minute", 5)).middleware],
    )
    async def create_user_endpoint(
        self,
        data: Annotated[
            CreateUserData,
            Body(title="Create user", description="`Create user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> dto.Id[uuid.UUID]:
        return await command_bus(
            request.state.ctx,
            commands.user.create.CreateUserCommand(data=data),
        )
