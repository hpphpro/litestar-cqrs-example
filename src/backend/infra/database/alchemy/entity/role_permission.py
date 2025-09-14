import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from backend.app.contracts.auth import Scope
from backend.infra.database.alchemy.entity.base.core import pascal_to_snake

from .base import Entity, mixins


class RolePermission(mixins.WithTimeMixin, Entity):
    role_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    permission_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("permission.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    scope: orm.Mapped[Scope] = orm.mapped_column(
        sa.Enum(Scope, native_enum=False, name=pascal_to_snake(Scope)),
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (sa.Index(None, "permission_id"),)
