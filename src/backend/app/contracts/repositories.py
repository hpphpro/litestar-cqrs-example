from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, Unpack, runtime_checkable

from .auth import Permission as AuthPermission
from .pagination import OffsetPaginationResult, SortOrder
from .result import AppResult
from .types import rbac, user


if TYPE_CHECKING:
    from backend.app import dto


@runtime_checkable
class UserRepository(Protocol):
    async def get_one(
        self,
        **filters: Unpack[user.FilterOneUser],
    ) -> AppResult[dto.user.UserPublic]: ...
    async def get_many_by_offset(
        self,
        offset: int,
        limit: int,
        order_by: SortOrder = "ASC",
        **filters: Unpack[user.FilterManyUser],
    ) -> AppResult[OffsetPaginationResult[dto.user.UserPublic]]: ...
    async def create(self, data: user.CreateUserData) -> AppResult[dto.user.UserPublic]: ...
    async def update(
        self,
        data: user.UpdateUserData,
        **filters: Unpack[user.FilterOneUser],
    ) -> AppResult[dto.user.UserPublic]: ...
    async def delete(
        self,
        **filters: Unpack[user.FilterOneUser],
    ) -> AppResult[dto.user.UserPublic]: ...


@runtime_checkable
class RbacRepository(Protocol):
    async def create_role(
        self,
        **data: Unpack[rbac.CreateRoleData],
    ) -> AppResult[dto.rbac.Role]: ...
    async def get_roles(self) -> AppResult[Sequence[dto.rbac.Role]]: ...
    async def update_role(
        self,
        role_id: uuid.UUID,
        **data: Unpack[rbac.UpdateRoleData],
    ) -> AppResult[bool]: ...
    async def delete_role(self, role_id: uuid.UUID) -> AppResult[bool]: ...
    async def set_role(self, **data: Unpack[rbac.RoleUserData]) -> AppResult[bool]: ...
    async def unset_role(self, **data: Unpack[rbac.RoleUserData]) -> AppResult[bool]: ...
    async def get_user_roles(self, user_id: uuid.UUID) -> AppResult[Sequence[dto.rbac.Role]]: ...
    async def get_role_users(
        self,
        role_id: uuid.UUID,
    ) -> AppResult[Sequence[dto.user.UserPublic]]: ...
    async def get_user_permissions(
        self, user_id: uuid.UUID
    ) -> AppResult[Sequence[AuthPermission]]: ...
    async def get_permissions(self) -> AppResult[Sequence[dto.rbac.Permission]]: ...
    async def grant_permission(
        self,
        **data: Unpack[rbac.GrantRolePermissionData],
    ) -> AppResult[bool]: ...
    async def revoke_permission(
        self,
        **data: Unpack[rbac.RevokeRolePermissionData],
    ) -> AppResult[bool]: ...
    async def grant_permission_field(
        self,
        **data: Unpack[rbac.GrantRolePermissionFieldData],
    ) -> AppResult[bool]: ...
    async def revoke_permission_field(
        self,
        **data: Unpack[rbac.RevokeRolePermissionFieldData],
    ) -> AppResult[bool]: ...
    async def update_permission_field_effect(
        self,
        data: rbac.UpdateRolePermissionFieldData,
        **filters: Unpack[rbac.RolePermissionFieldFilter],
    ) -> AppResult[bool]: ...
