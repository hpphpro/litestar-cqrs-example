import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from .base import Entity


class UserRole(Entity):
    user_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    role_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    @orm.declared_attr.directive
    def __table_args__(self) -> Any:
        return (sa.Index(None, "role_id"),)
