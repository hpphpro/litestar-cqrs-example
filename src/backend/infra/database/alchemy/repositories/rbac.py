import uuid
from collections.abc import Sequence
from typing import Unpack

from backend.app import dto
from backend.app.contracts.auth import Permission as AuthPermission
from backend.app.contracts.types import rbac
from backend.infra.database.alchemy import entity, queries
from backend.infra.shared.result import as_result

from .base import UnboundRepository


class RbacRepositoryImpl(UnboundRepository):
    @as_result()
    async def create_role(self, **data: Unpack[rbac.CreateRoleData]) -> dto.rbac.Role | None:
        result = await self.manager.send(queries.base.CreateOrIgnore[entity.Role](**data))

        return dto.rbac.Role.from_attributes(result) if result else None

    @as_result()
    async def get_roles(self) -> Sequence[dto.rbac.Role]:
        result = await self.manager.send(queries.base.GetAll[entity.Role]("fields"))

        return [dto.rbac.Role.from_attributes(item) for item in result]

    @as_result()
    async def update_role(self, role_id: uuid.UUID, **data: Unpack[rbac.UpdateRoleData]) -> bool:
        result = await self.manager.send(queries.base.Update[entity.Role](data, id=role_id))

        return len(result) > 0

    @as_result()
    async def delete_role(self, role_id: uuid.UUID) -> bool:
        result = await self.manager.send(queries.base.Delete[entity.Role](id=role_id))

        return len(result) > 0

    @as_result()
    async def set_role(self, **data: Unpack[rbac.RoleUserData]) -> bool:
        result = await self.manager.send(queries.base.CreateOrIgnore[entity.UserRole](**data))

        return bool(result)

    @as_result()
    async def unset_role(self, **data: Unpack[rbac.RoleUserData]) -> bool:
        result = await self.manager.send(queries.base.Delete[entity.UserRole](**data))

        return len(result) > 0

    @as_result()
    async def get_user_roles(self, user_id: uuid.UUID) -> Sequence[dto.rbac.Role]:
        result = await self.manager.send(queries.rbac.GetUserRoles(user_id))

        return [dto.rbac.Role.from_attributes(item) for item in result]

    @as_result()
    async def get_role_users(self, role_id: uuid.UUID) -> Sequence[dto.user.UserPrivate]:
        result = await self.manager.send(queries.rbac.GetRoleUsers(role_id))

        return [dto.user.UserPrivate.from_attributes(item) for item in result]

    @as_result()
    async def get_permissions(self) -> Sequence[dto.rbac.Permission]:
        result = await self.manager.send(queries.base.GetAll[entity.Permission]("fields", "roles"))

        return [dto.rbac.Permission.from_attributes(item) for item in result]

    @as_result()
    async def get_user_permissions(self, user_id: uuid.UUID) -> Sequence[AuthPermission]:
        return await self.manager.send(queries.user.GetUserPermissions(user_id))

    @as_result()
    async def grant_permission(
        self,
        **data: Unpack[rbac.GrantRolePermissionData],
    ) -> bool:
        result = await self.manager.send(queries.base.CreateOrIgnore[entity.RolePermission](**data))

        return bool(result)

    @as_result()
    async def revoke_permission(self, **data: Unpack[rbac.RevokeRolePermissionData]) -> bool:
        result = await self.manager.send(queries.base.Delete[entity.RolePermission](**data))

        return len(result) > 0

    @as_result()
    async def grant_permission_field(
        self, **data: Unpack[rbac.GrantRolePermissionFieldData]
    ) -> bool:
        result = await self.manager.send(
            queries.base.CreateOrIgnore[entity.RolePermissionField](**data)
        )

        return bool(result)

    @as_result()
    async def revoke_permission_field(
        self, **data: Unpack[rbac.RevokeRolePermissionFieldData]
    ) -> bool:
        result = await self.manager.send(queries.base.Delete[entity.RolePermissionField](**data))

        return len(result) > 0

    @as_result()
    async def update_permission_field_effect(
        self,
        data: rbac.UpdateRolePermissionFieldData,
        **filters: Unpack[rbac.RolePermissionFieldFilter],
    ) -> bool:
        result = await self.manager.send(
            queries.base.Update[entity.RolePermissionField](data, **filters)
        )

        return len(result) > 0
