from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from backend.app.contracts.auth import Action
from backend.infra.database.alchemy.entity.base.core import pascal_to_snake

from . import permission_field, role
from .base import Entity, mixins
from .role_permission import RolePermission


class Permission(mixins.WithUUIDMixin, Entity):
    resource: orm.Mapped[str] = orm.mapped_column()
    action: orm.Mapped[Action] = orm.mapped_column(
        sa.Enum(Action, native_enum=False, name=pascal_to_snake(Action)),
    )
    operation: orm.Mapped[str] = orm.mapped_column()
    description: orm.Mapped[str | None] = orm.mapped_column(nullable=True)
    key: orm.Mapped[str] = orm.mapped_column(
        sa.Text,
        sa.Computed(
            "lower(resource::text) || ':' || lower(action::text) || ':' || lower(operation::text)",
        ),
    )

    # relationships
    roles: orm.Mapped[list[role.Role]] = orm.relationship(
        "Role",
        primaryjoin="Permission.id == foreign(RolePermission.permission_id)",
        secondaryjoin="foreign(RolePermission.role_id) == Role.id",
        secondary=RolePermission.__table__,
        back_populates="permissions",
        lazy="noload",
    )
    fields: orm.Mapped[list[permission_field.PermissionField]] = orm.relationship(
        "PermissionField",
        primaryjoin="Permission.id == foreign(PermissionField.permission_id)",
        back_populates="permission",
        lazy="noload",
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (sa.Index(None, self.key, unique=True),)
