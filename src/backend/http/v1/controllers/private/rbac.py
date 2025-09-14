import uuid
from collections.abc import Sequence
from typing import Annotated

from litestar import Controller, MediaType, Request, delete, get, post, status_codes
from litestar.datastructures import State
from litestar.handlers.http_handlers import patch
from litestar.params import Body

from backend.app import dto
from backend.app.contracts.auth import (
    Action,
    AuthUser,
    PermissionSpec,
    Source,
    TokenClaims,
)
from backend.app.contracts.auth import (
    Permission as AuthPermission,
)
from backend.app.contracts.types import rbac
from backend.app.use_cases import commands, queries
from backend.http.common import docs
from backend.http.common.tools import (
    RouteRule,
    add_rule,
    get_keys_from_type,
)
from backend.http.common.tools.resolvers.default import resolve_keys_allowed_denylist


class RbacController(Controller):
    path = "/rbac"
    tags = ["rbac"]
    security = [{"BearerToken": []}]

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.CREATE,
                operation="create-role",
                description="Create a new role",
                fields={
                    Source.JSON: get_keys_from_type(rbac.CreateRoleData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        )
    )
    @post(
        "/roles",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def create_role_endpoint(
        self,
        data: Annotated[
            rbac.CreateRoleData,
            Body(title="Create role", description="`Create role`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Id[uuid.UUID]:
        return await command_bus(
            request.state.ctx,
            commands.rbac.create.CreateRoleCommand(data=data),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.READ,
                operation="get-roles",
                description="Get all roles",
            ),
        )
    )
    @get(
        "/roles",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer.to_spec() | docs.Forbidden.to_spec(),
    )
    async def get_roles_endpoint(
        self,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> Sequence[dto.rbac.Role]:
        return await query_bus(
            request.state.ctx,
            queries.rbac.get.GetAllRolesQuery(),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.READ,
                operation="get-user-roles",
                description="Get a user roles",
            ),
        )
    )
    @get(
        "/users/{user_id:uuid}/roles",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def get_user_roles_endpoint(
        self,
        user_id: uuid.UUID,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> Sequence[dto.rbac.Role]:
        return await query_bus(
            request.state.ctx,
            queries.rbac.get.GetUserRolesQuery(user_id=user_id),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.READ,
                operation="get-user-permissions",
                description="Get a user permissions",
            ),
        )
    )
    @get(
        "/users/{user_id:uuid}/permissions",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def get_user_permissions_endpoint(
        self,
        user_id: uuid.UUID,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> Sequence[AuthPermission]:
        return await query_bus(
            request.state.ctx,
            queries.rbac.get.GetUserPermissionsQuery(user_id=user_id),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.READ,
                operation="get-role-users",
                description="Get a role users",
            ),
        )
    )
    @get(
        "/roles/{role_id:uuid}/users",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def get_role_users_endpoint(
        self,
        role_id: uuid.UUID,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> Sequence[dto.user.UserPrivate]:
        return await query_bus(
            request.state.ctx,
            queries.rbac.get.GetRoleUsersQuery(role_id=role_id),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.READ,
                operation="list-permissions",
                description="List all permissions",
            ),
        )
    )
    @get(
        "/permissions",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def list_permissions_endpoint(
        self,
        query_bus: queries.QueryBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> Sequence[dto.rbac.Permission]:
        return await query_bus(
            request.state.ctx,
            queries.rbac.get.GetAllPermissionsQuery(),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.UPDATE,
                operation="update-role",
                description="Update a role",
                fields={
                    Source.JSON: get_keys_from_type(rbac.UpdateRoleData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        )
    )
    @patch(
        "/roles/{role_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def update_role_endpoint(
        self,
        role_id: uuid.UUID,
        data: Annotated[
            rbac.UpdateRoleData,
            Body(title="Update role", description="`Update role`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.update.UpdateRoleCommand(role_id=role_id, data=data),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.UPDATE,
                operation="update-role-permission",
                description="Update a role permission",
                fields={
                    Source.JSON: get_keys_from_type(rbac.UpdateRolePermissionFieldData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        )
    )
    @patch(
        "/roles/{role_id:uuid}/permissions/{permission_id:uuid}/fields/{field_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def update_role_permission_endpoint(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        field_id: uuid.UUID,
        data: Annotated[
            rbac.UpdateRolePermissionFieldData,
            Body(
                title="Update role permission field", description="`Update role permission field`"
            ),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.update.UpdatePermissionFieldCommand(
                filters=rbac.RolePermissionFieldFilter(
                    role_id=role_id, permission_id=permission_id, field_id=field_id
                ),
                data=data,
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.CREATE,
                operation="set-role",
                description="Set a role",
            ),
        )
    )
    @post(
        "/roles/{role_id:uuid}/users/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def set_role_endpoint(
        self,
        role_id: uuid.UUID,
        user_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.create.SetRoleCommand(
                data=rbac.RoleUserData(role_id=role_id, user_id=user_id)
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.CREATE,
                operation="grant-permission",
                description="Grant a permission",
                fields={
                    Source.JSON: get_keys_from_type(rbac.GrantRolePermissionData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        )
    )
    @post(
        "/permissions",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def grant_permission_endpoint(
        self,
        data: Annotated[
            rbac.GrantRolePermissionData,
            Body(title="Grant permission", description="`Grant permission`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.create.GrantPermissionCommand(
                data=data,
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.CREATE,
                operation="grant-permission-field",
                description="Grant a permission field",
                fields={
                    Source.JSON: get_keys_from_type(rbac.GrantRolePermissionFieldData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        ),
    )
    @post(
        "/permission-fields",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def grant_permission_field_endpoint(
        self,
        data: Annotated[
            rbac.GrantRolePermissionFieldData,
            Body(title="Grant permission field", description="`Grant permission field`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.create.GrantPermissionFieldCommand(data=data),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.CREATE,
                operation="grant-role-permission",
                description="Grant a role permission",
                fields={
                    Source.JSON: get_keys_from_type(rbac.GrantRolePermissionData),
                },
            ),
            check_fields=resolve_keys_allowed_denylist,
        ),
    )
    @post(
        "/role-permissions",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_201_CREATED,
        responses=docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def grant_role_permission_endpoint(
        self,
        data: Annotated[
            rbac.GrantRolePermissionData,
            Body(title="Grant role permission", description="`Grant role permission`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> dto.Status:
        return await command_bus(
            request.state.ctx,
            commands.rbac.create.GrantRolePermissionCommand(data=data),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.DELETE,
                operation="unset-role",
                description="Unset a role",
            ),
        )
    )
    @delete(
        "/roles/{role_id:uuid}/users/{user_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_204_NO_CONTENT,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def delete_role_endpoint(
        self,
        role_id: uuid.UUID,
        user_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> None:
        await command_bus(
            request.state.ctx,
            commands.rbac.delete.UnsetRoleCommand(
                data=rbac.RoleUserData(role_id=role_id, user_id=user_id)
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.DELETE,
                operation="revoke-permission",
                description="Revoke a permission",
            ),
        )
    )
    @delete(
        "/roles/{role_id:uuid}/permissions/{permission_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_204_NO_CONTENT,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def revoke_permission_endpoint(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> None:
        await command_bus(
            request.state.ctx,
            commands.rbac.delete.RevokePermissionCommand(
                data=rbac.RevokeRolePermissionData(role_id=role_id, permission_id=permission_id)
            ),
        )

    @add_rule(
        RouteRule(
            permission=PermissionSpec(
                resource="rbac",
                action=Action.DELETE,
                operation="revoke-permission-field",
                description="Revoke a permission field",
            ),
        )
    )
    @delete(
        "/roles/{role_id:uuid}/permissions/{permission_id:uuid}/fields/{field_id:uuid}",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_204_NO_CONTENT,
        responses=docs.NotFound.to_spec()
        | docs.InternalServer.to_spec()
        | docs.Conflict.to_spec()
        | docs.Forbidden.to_spec(),
    )
    async def revoke_permission_field_endpoint(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        field_id: uuid.UUID,
        command_bus: commands.CommandBus,
        request: Request[AuthUser, TokenClaims, State],
    ) -> None:
        await command_bus(
            request.state.ctx,
            commands.rbac.delete.RevokePermissionFieldCommand(
                data=rbac.RevokeRolePermissionFieldData(
                    role_id=role_id, permission_id=permission_id, field_id=field_id
                )
            ),
        )
