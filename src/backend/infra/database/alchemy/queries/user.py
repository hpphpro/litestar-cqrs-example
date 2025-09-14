import uuid
from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.auth import Action, Permission, Scope, Source
from backend.infra.database.alchemy import entity

from .base import ExtendedQuery


class GetUserPermission(ExtendedQuery[entity.User, Permission | None]):
    __slots__ = (
        "permission_key",
        "user_id",
    )

    def __init__(self, user_id: uuid.UUID, permission_key: str) -> None:
        self.user_id = user_id
        self.permission_key = permission_key

    @override
    async def __call__(self, session: AsyncSession, /, **kw: Any) -> Permission | None:
        result = await session.execute(
            sa.select(
                sa.text(
                    "resource, action, operation, scope, description, allow_fields, deny_fields"
                )
            )
            .select_from(sa.text("mv_user_permissions"))
            .where(
                sa.text("user_id = :user_id"),
                sa.text("permission_key = :permission_key"),
            ),
            params={"user_id": self.user_id, "permission_key": self.permission_key},
        )

        data = result.mappings().first()

        if not data:
            return None

        return Permission(
            resource=data["resource"],
            action=Action(data["action"].lower()),
            operation=data["operation"],
            scope=Scope(data["scope"].lower()),
            description=data["description"],
            allow_fields={Source(k.lower()): frozenset(v) for k, v in data["allow_fields"].items()},
            deny_fields={Source(k.lower()): frozenset(v) for k, v in data["deny_fields"].items()},
        )


class GetUserPermissions(ExtendedQuery[entity.User, Sequence[Permission]]):
    __slots__ = ("user_id",)

    def __init__(self, user_id: uuid.UUID) -> None:
        self.user_id = user_id

    @override
    async def __call__(self, session: AsyncSession, /, **kw: Any) -> Sequence[Permission]:
        result = await session.execute(
            sa.select(
                sa.text(
                    "resource, action, operation, scope, description, allow_fields, deny_fields"
                )
            )
            .select_from(sa.text("mv_user_permissions"))
            .where(
                sa.text("user_id = :user_id"),
            ),
            params={"user_id": self.user_id},
        )

        return [
            Permission(
                resource=data["resource"],
                action=Action(data["action"].lower()),
                operation=data["operation"],
                scope=Scope(data["scope"].lower()),
                description=data["description"],
                allow_fields={
                    Source(k.lower()): frozenset(v) for k, v in data["allow_fields"].items()
                },
                deny_fields={
                    Source(k.lower()): frozenset(v) for k, v in data["deny_fields"].items()
                },
            )
            for data in result.mappings().all()
        ]
