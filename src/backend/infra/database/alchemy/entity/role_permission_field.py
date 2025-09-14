from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from backend.app.contracts.auth import Effect
from backend.infra.database.alchemy.entity.base.core import pascal_to_snake

from . import permission, permission_field, role
from .base import Entity, mixins


class RolePermissionField(mixins.WithTimeMixin, Entity):
    role_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    permission_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("permission.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    field_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("permission_field.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    effect: orm.Mapped[Effect] = orm.mapped_column(
        sa.Enum(Effect, native_enum=False, name=pascal_to_snake(Effect)),
    )

    # relationships
    permission: orm.Mapped[permission.Permission] = orm.relationship(
        "Permission",
        primaryjoin="foreign(RolePermissionField.permission_id) == Permission.id",
        lazy="noload",
        viewonly=True,
    )
    role: orm.Mapped[role.Role] = orm.relationship(
        "Role",
        primaryjoin="foreign(RolePermissionField.role_id) == Role.id",
        lazy="noload",
        viewonly=True,
    )
    field: orm.Mapped[permission_field.PermissionField] = orm.relationship(
        "PermissionField",
        primaryjoin="foreign(RolePermissionField.field_id) == PermissionField.id",
        lazy="noload",
        viewonly=True,
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (
            sa.Index(None, "permission_id"),
            sa.Index(None, "field_id"),
        )
