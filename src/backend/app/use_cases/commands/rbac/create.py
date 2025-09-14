import uuid
from dataclasses import dataclass
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types import rbac


class CreateRoleCommand(dto.BaseDTO):
    data: rbac.CreateRoleData


@dataclass(frozen=True, slots=True)
class CreateRoleCommandHandler(Handler[Context, CreateRoleCommand, dto.Id[uuid.UUID]]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: CreateRoleCommand, /) -> dto.Id[uuid.UUID]:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.create_role(**qc.data)

        return dto.Id(
            id=result.map_err(exc.ConflictError.from_other).unwrap().id,
        )


class GrantRolePermissionCommand(dto.BaseDTO):
    data: rbac.GrantRolePermissionData


@dataclass(frozen=True, slots=True)
class GrantRolePermissionCommandHandler(Handler[Context, GrantRolePermissionCommand, dto.Status]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GrantRolePermissionCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.grant_permission(**qc.data)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())


class SetRoleCommand(dto.BaseDTO):
    data: rbac.RoleUserData


@dataclass(frozen=True, slots=True)
class SetRoleCommandHandler(Handler[Context, SetRoleCommand, dto.Status]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: SetRoleCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.set_role(**qc.data)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())


class GrantPermissionCommand(dto.BaseDTO):
    data: rbac.GrantRolePermissionData


@dataclass(frozen=True, slots=True)
class GrantPermissionCommandHandler(Handler[Context, GrantPermissionCommand, dto.Status]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GrantPermissionCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.grant_permission(**qc.data)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())


class GrantPermissionFieldCommand(dto.BaseDTO):
    data: rbac.GrantRolePermissionFieldData


@dataclass(frozen=True, slots=True)
class GrantPermissionFieldCommandHandler(Handler[Context, GrantPermissionFieldCommand, dto.Status]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: GrantPermissionFieldCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.grant_permission_field(**qc.data)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())
