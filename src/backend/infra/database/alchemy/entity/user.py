from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from . import role
from .base import Entity, mixins
from .user_role import UserRole


class User(mixins.WithUUIDMixin, mixins.WithTimeMixin, Entity):
    email: orm.Mapped[str | None] = orm.mapped_column(nullable=True)
    password: orm.Mapped[str | None] = orm.mapped_column(nullable=True)

    # relationships
    roles: orm.Mapped[list[role.Role]] = orm.relationship(
        "Role",
        primaryjoin="User.id == foreign(UserRole.user_id)",
        secondaryjoin="foreign(UserRole.role_id) == Role.id",
        secondary=UserRole.__table__,
        back_populates="users",
        lazy="noload",
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (sa.Index(None, sa.func.lower(self.email), unique=True),)
