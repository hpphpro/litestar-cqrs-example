import uuid
from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infra.database.alchemy import entity

from . import base


class GetRoleUsers(base.ExtendedQuery[entity.User, Sequence[entity.User]]):
    __slots__ = ("role_id",)

    def __init__(self, role_id: uuid.UUID) -> None:
        self.role_id = role_id

    @override
    async def __call__(self, session: AsyncSession, /, **kw: Any) -> Sequence[entity.User]:
        stmt = (
            sa.select(entity.User)
            .join(entity.UserRole)
            .where(entity.UserRole.role_id == self.role_id)
        )

        return (await session.scalars(stmt)).unique().all()


class GetUserRoles(base.ExtendedQuery[entity.Role, Sequence[entity.Role]]):
    __slots__ = ("user_id",)

    def __init__(self, user_id: uuid.UUID) -> None:
        self.user_id = user_id

    @override
    async def __call__(self, session: AsyncSession, /, **kw: Any) -> Sequence[entity.Role]:
        stmt = (
            sa.select(entity.Role)
            .join(entity.UserRole)
            .where(entity.UserRole.user_id == self.user_id)
        )

        return (await session.scalars(stmt)).unique().all()
