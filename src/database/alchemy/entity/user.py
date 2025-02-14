from typing import Any

import sqlalchemy as sa
from sqlalchemy import orm

from src.database.alchemy.entity.base import Entity, mixins


class User(mixins.WithUUIDMixin, mixins.WithTimeMixin, Entity):
    login: orm.Mapped[str] = orm.mapped_column()
    password: orm.Mapped[str]

    @orm.declared_attr.directive
    def __table_args__(cls) -> Any:
        return (
            sa.Index(f"idx_{cls.__tablename__}_login_lower", sa.func.lower(cls.login), unique=True),
        )
