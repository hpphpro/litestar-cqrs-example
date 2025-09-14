import re
from dataclasses import asdict
from typing import Any, Final

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


PASCAL_TO_SNAKE_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<!^)(?=[A-Z])")

CONVENTION: Final[dict[str, str]] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _filter_none(values: list[tuple[str, Any]]) -> dict[str, Any]:
    return {k: v for k, v in values if v is not None}


def pascal_to_snake(obj: Any) -> str:
    return PASCAL_TO_SNAKE_PATTERN.sub("_", getattr(obj, "__name__", "")).lower()


class Entity(MappedAsDataclass, DeclarativeBase, init=False):
    metadata = MetaData(naming_convention=CONVENTION)

    @declared_attr.directive
    def __tablename__(self) -> str:
        return pascal_to_snake(self)

    def as_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        return asdict(self, dict_factory=_filter_none) if exclude_none else asdict(self)
