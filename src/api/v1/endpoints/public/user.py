import uuid
from typing import Annotated

from litestar import Controller, MediaType, Request, delete, get, patch, post, status_codes
from litestar.datastructures import State
from litestar.params import Body, Parameter

from src.api.common import docs
from src.api.common.tools import page_to_offset
from src.api.v1 import commands, dto, queries
from src.api.v1.endpoints.constants import MAX_PAGINATION_LIMIT, MIN_PAGINATION_LIMIT
from src.database.alchemy.types import OrderBy


class UserController(Controller):
    path = "/users"
    tags = ["user"]

    @post(
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.Conflict().to_spec()
        | docs.InternalServer().to_spec()
        | docs.TooManyRequests().to_spec(),
    )
    async def create_user_endpoint(
        self,
        data: Annotated[
            commands.user.create.CreateUser,
            Body(title="Create user", description="`Create user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> dto.user.User:
        return await command_bus(request, data)

    @get(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound().to_spec() | docs.InternalServer().to_spec(),
    )
    async def get_one_user_endpoint(
        self,
        user_id: uuid.UUID,
        query_bus: queries.QueryBus,
        request: Request[None, None, State],
    ) -> dto.user.User:
        return await query_bus(request, queries.user.get.GetOneUser(user_id))

    @get(
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer().to_spec(),
    )
    async def get_many_by_offset_endpoint(
        self,
        order_by: Annotated[
            OrderBy, Parameter(default="ASC", required=False, description="`sorting` strategy")
        ],
        page: Annotated[int, Parameter(default=1, required=False, description="Current `page`")],
        limit: Annotated[
            int,
            Parameter(
                default=MIN_PAGINATION_LIMIT,
                le=MAX_PAGINATION_LIMIT,
                ge=MIN_PAGINATION_LIMIT,
                required=False,
                description="Items limit",
            ),
        ],
        query_bus: queries.QueryBus,
        request: Request[None, None, State],
    ) -> dto.OffsetResult[dto.user.User]:
        return await query_bus(
            request,
            queries.user.get.GetManyOffsetUser(
                offset=page_to_offset(page, limit), limit=limit, order_by=order_by
            ),
        )

    @patch(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound().to_spec() | docs.InternalServer().to_spec(),
    )
    async def update_user_by_id_endpoint(
        self,
        user_id: uuid.UUID,
        data: Annotated[
            commands.user.update.UpdateUser,
            Body(title="Update user", description="`Update user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> dto.Status:
        return await command_bus(request, data, id=user_id)

    @delete(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_204_NO_CONTENT,
        responses=docs.NotFound().to_spec() | docs.InternalServer().to_spec(),
    )
    async def delete_user_by_id_endpoint(
        self,
        user_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> None:
        await command_bus(request, commands.user.delete.DeleteUser(id=user_id))
