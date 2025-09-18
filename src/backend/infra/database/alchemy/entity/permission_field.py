from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from backend.app.contracts.auth import Source
from backend.infra.database.alchemy.entity.base.core import pascal_to_snake

from . import permission
from .base import Entity, mixins


class PermissionField(mixins.WithUUIDMixin, Entity):
    permission_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("permission.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    src: orm.Mapped[Source] = orm.mapped_column(
        sa.Enum(Source, native_enum=False, name=pascal_to_snake(Source)),
    )
    name: orm.Mapped[str] = orm.mapped_column()

    # relationships
    permission: orm.Mapped[permission.Permission | None] = orm.relationship(
        "Permission",
        primaryjoin="foreign(PermissionField.permission_id) == Permission.id",
        back_populates="fields",
        lazy="noload",
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (
            sa.Index(
                None,
                "permission_id",
                sa.func.lower(self.src),
                sa.func.lower(self.name),
                unique=True,
            ),
        )
