from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types import rbac
from backend.app.use_cases.transform import handler


class UnsetRoleCommand(dto.BaseDTO):
    data: rbac.RoleUserData


@handler
class UnsetRoleCommandHandler(Handler[Context, UnsetRoleCommand, None]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: UnsetRoleCommand, /) -> None:
        async with await self.gateway.manager.with_transaction():
            (await self.gateway.rbac.unset_role(**qc.data)).map_err(
                exc.ConflictError.from_other
            ).unwrap()


class RevokePermissionCommand(dto.BaseDTO):
    data: rbac.RevokeRolePermissionData


@handler
class RevokePermissionCommandHandler(Handler[Context, RevokePermissionCommand, None]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: RevokePermissionCommand, /) -> None:
        async with await self.gateway.manager.with_transaction():
            (await self.gateway.rbac.revoke_permission(**qc.data)).map_err(
                exc.ConflictError.from_other
            ).unwrap()


class RevokePermissionFieldCommand(dto.BaseDTO):
    data: rbac.RevokeRolePermissionFieldData


@handler
class RevokePermissionFieldCommandHandler(Handler[Context, RevokePermissionFieldCommand, None]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: RevokePermissionFieldCommand, /) -> None:
        async with await self.gateway.manager.with_transaction():
            (await self.gateway.rbac.revoke_permission_field(**qc.data)).map_err(
                exc.ConflictError.from_other
            ).unwrap()
