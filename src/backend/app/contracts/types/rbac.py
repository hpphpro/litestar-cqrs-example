import uuid
from typing import TypedDict

from backend.app.contracts.auth import Effect, Scope


class RolePermissionFieldFilter(TypedDict, total=False):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    field_id: uuid.UUID


class RolePermissionFilter(TypedDict, total=False):
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RoleUserData(TypedDict):
    role_id: uuid.UUID
    user_id: uuid.UUID


class UpdateRoleData(TypedDict, total=False):
    name: str
    level: int
    is_superuser: bool


class UpdateRolePermissionFieldData(TypedDict, total=False):
    effect: Effect


class GrantRolePermissionFieldData(TypedDict):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    field_id: uuid.UUID
    effect: Effect


class RevokeRolePermissionFieldData(TypedDict):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    field_id: uuid.UUID


class CreateRoleData(TypedDict):
    name: str
    level: int
    is_superuser: bool


class GrantRolePermissionData(TypedDict):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    scope: Scope


class RevokeRolePermissionData(TypedDict):
    role_id: uuid.UUID
    permission_id: uuid.UUID
