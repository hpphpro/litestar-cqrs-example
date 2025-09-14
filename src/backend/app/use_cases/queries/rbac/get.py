import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.auth import Permission as AuthPermission
from backend.app.contracts.gateway import RepositoryGateway


class GetUserPermissionsQuery(dto.BaseDTO):
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class GetUserPermissionsQueryHandler(
    Handler[Context, GetUserPermissionsQuery, Sequence[AuthPermission]]
):
    gateway: RepositoryGateway

    @override
    async def __call__(
        self, ctx: Context, qc: GetUserPermissionsQuery, /
    ) -> Sequence[AuthPermission]:
        async with self.gateway.manager:
            result = await self.gateway.rbac.get_user_permissions(qc.user_id)

        return result.map_err(exc.ServiceNotImplementedError.from_other).unwrap()


class GetAllPermissionsQuery(dto.BaseDTO):
    pass


@dataclass(frozen=True, slots=True)
class GetPermissionsQueryHandler(
    Handler[Context, GetAllPermissionsQuery, Sequence[dto.rbac.Permission]]
):
    gateway: RepositoryGateway

    @override
    async def __call__(
        self, ctx: Context, qc: GetAllPermissionsQuery, /
    ) -> Sequence[dto.rbac.Permission]:
        async with self.gateway.manager:
            result = await self.gateway.rbac.get_permissions()

        return result.map_err(exc.ServiceNotImplementedError.from_other).unwrap()


class GetUserRolesQuery(dto.BaseDTO):
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class GetUserRolesQueryHandler(Handler[Context, GetUserRolesQuery, Sequence[dto.rbac.Role]]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GetUserRolesQuery, /) -> Sequence[dto.rbac.Role]:
        async with self.gateway.manager:
            result = await self.gateway.rbac.get_user_roles(qc.user_id)

        return result.map_err(exc.ServiceNotImplementedError.from_other).unwrap()


class GetRoleUsersQuery(dto.BaseDTO):
    role_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class GetRoleUsersQueryHandler(Handler[Context, GetRoleUsersQuery, Sequence[dto.user.UserPrivate]]):
    gateway: RepositoryGateway

    @override
    async def __call__(
        self, ctx: Context, qc: GetRoleUsersQuery, /
    ) -> Sequence[dto.user.UserPrivate]:
        async with self.gateway.manager:
            result = await self.gateway.rbac.get_role_users(qc.role_id)

        return result.map_err(exc.ServiceNotImplementedError.from_other).unwrap()


class GetAllRolesQuery(dto.BaseDTO):
    pass


@dataclass(frozen=True, slots=True)
class GetAllRolesQueryHandler(Handler[Context, GetAllRolesQuery, Sequence[dto.rbac.Role]]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GetAllRolesQuery, /) -> Sequence[dto.rbac.Role]:
        async with self.gateway.manager:
            result = await self.gateway.rbac.get_roles()

        return result.map_err(exc.ServiceNotImplementedError.from_other).unwrap()
