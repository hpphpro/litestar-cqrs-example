import uuid
from typing import Annotated

from litestar import Controller, MediaType, Request, delete, get, patch, status_codes
from litestar.datastructures import State
from litestar.di import Provide
from litestar.params import Body

from backend.app import dto
from backend.app.contracts.auth import Action, AuthUser, PermissionSpec, Source, TokenClaims
from backend.app.contracts.types.user import (
    FilterManyUser,
    FilterOneUser,
    UpdateUserData,
)
from backend.app.use_cases import commands, queries
from backend.http.common import docs
from backend.http.common.dto import PagedOffsetPagination
from backend.http.common.tools import (
    RouteRule,
    ToOwned,
    add_rule,
    get_keys_from_type,
    make_filter_query,
)
from backend.http.common.tools.resolvers.default import resolve_keys_allowed_denylist
from backend.http.common.tools.resolvers.user import resolve_by_user_email, resolve_by_user_id


class UserController(Controller):
    path = "/users"
    tags = ["user"]
    security = [{"BearerToken": []}]

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="users",
                action=Action.READ,
                operation="detail",
                description="Get one user by id",
            ),
            check_scope=resolve_by_user_id,
        )
    )
    @get(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec() | docs.InternalServer.to_spec(),
    )
    async def get_one_user_endpoint(
        self,
        user_id: uuid.UUID,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.user.UserPublic:
        return await query_bus(
            request.state.ctx,
            queries.user.get.GetOneUserQuery(filters=FilterOneUser(id=user_id)),
        )

    @get(
        "/me",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec() | docs.InternalServer.to_spec(),
    )
    async def get_user_me_endpoint(
        self,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.user.UserPublic:
        return await query_bus(
            request.state.ctx,
            queries.user.get.GetOneUserQuery(filters=FilterOneUser(id=request.user.id)),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="users",
                action=Action.READ,
                operation="list",
                description="Get many users by offset",
                fields={
                    Source.QUERY: get_keys_from_type(FilterManyUser),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
            check_scope=resolve_by_user_email,
        )
    )
    @get(
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer.to_spec(),
        dependencies={
            "params": Provide(make_filter_query(FilterManyUser), sync_to_thread=False),
            "pagination": Provide(PagedOffsetPagination, sync_to_thread=False),
        },
    )
    async def get_many_by_offset_endpoint(
        self,
        pagination: PagedOffsetPagination,
        params: ToOwned[FilterManyUser],
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.OffsetResult[dto.user.UserPublic]:
        return await query_bus(
            request.state.ctx,
            queries.user.get.GetManyOffsetUserQuery(
                pagination=pagination.to_offset_pagination(), filters=params.to_owned()
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="users",
                action=Action.UPDATE,
                operation="update",
                description="Update one user by id",
                fields={
                    Source.JSON: get_keys_from_type(UpdateUserData),
                },
            ),
            check_scope=resolve_by_user_id,
            check_fields=resolve_keys_allowed_denylist,
        )
    )
    @patch(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec() | docs.InternalServer.to_spec(),
    )
    async def update_user_by_id_endpoint(
        self,
        user_id: uuid.UUID,
        data: Annotated[
            UpdateUserData,
            Body(title="Update user", description="`Update user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.user.update.UpdateUserCommand(filters=FilterOneUser(id=user_id), data=data),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="users",
                action=Action.DELETE,
                operation="delete",
                description="Delete one user by id",
            ),
            check_scope=resolve_by_user_id,
        )
    )
    @delete(
        "/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_204_NO_CONTENT,
        responses=docs.NotFound.to_spec() | docs.InternalServer.to_spec(),
    )
    async def delete_user_by_id_endpoint(
        self,
        user_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> None:
        await command_bus(
            request.state.ctx,
            commands.user.delete.DeleteUserCommand(filters=FilterOneUser(id=user_id)),
        )
