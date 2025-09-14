from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from . import permission, user
from .base import Entity, mixins
from .role_permission import RolePermission
from .user_role import UserRole


class Role(mixins.WithUUIDMixin, Entity):
    name: orm.Mapped[str] = orm.mapped_column()
    level: orm.Mapped[int] = orm.mapped_column()
    is_superuser: orm.Mapped[bool] = orm.mapped_column(
        insert_default=False,
        server_default=sa.False_(),
    )

    # relationships
    users: orm.Mapped[list[user.User]] = orm.relationship(
        user.User,
        primaryjoin="Role.id == foreign(UserRole.role_id)",
        secondaryjoin="foreign(UserRole.user_id) == User.id",
        secondary=UserRole.__table__,
        back_populates="roles",
        lazy="noload",
    )
    permissions: orm.Mapped[list[permission.Permission]] = orm.relationship(
        "Permission",
        primaryjoin="Role.id == foreign(RolePermission.role_id)",
        secondaryjoin="foreign(RolePermission.permission_id) == Permission.id",
        secondary=RolePermission.__table__,
        back_populates="roles",
        lazy="noload",
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (
            sa.Index(None, sa.func.lower(self.name), unique=True),
            sa.Index(
                None,
                "is_superuser",
                unique=True,
                postgresql_where=self.is_superuser == True,  # noqa: E712
            ),
        )
