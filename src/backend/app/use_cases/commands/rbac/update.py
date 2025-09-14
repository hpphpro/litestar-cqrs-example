import uuid
from dataclasses import dataclass
from typing import override

from backend.app import dto
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context
from backend.app.contracts.gateway import RepositoryGateway
from backend.app.contracts.types import rbac


class UpdateRoleCommand(dto.BaseDTO):
    role_id: uuid.UUID
    data: rbac.UpdateRoleData


@dataclass(frozen=True, slots=True)
class UpdateRoleCommandHandler(Handler[Context, UpdateRoleCommand, dto.Status]):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: UpdateRoleCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.update_role(qc.role_id, **qc.data)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())


class UpdatePermissionFieldCommand(dto.BaseDTO):
    filters: rbac.RolePermissionFieldFilter
    data: rbac.UpdateRolePermissionFieldData


@dataclass(frozen=True, slots=True)
class UpdatePermissionFieldCommandHandler(
    Handler[Context, UpdatePermissionFieldCommand, dto.Status]
):
    gateway: RepositoryGateway

    @override
    async def __call__(self, ctx: Context, qc: UpdatePermissionFieldCommand, /) -> dto.Status:
        async with await self.gateway.manager.with_transaction():
            result = await self.gateway.rbac.update_permission_field_effect(qc.data, **qc.filters)

        return dto.Status(status=result.map_err(exc.ConflictError.from_other).unwrap())
