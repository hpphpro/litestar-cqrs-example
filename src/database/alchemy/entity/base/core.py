import re
from dataclasses import asdict
from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


def _filter_none(values: list[tuple[str, Any]]) -> dict[str, Any]:
    return {k: v for k, v in values if v is not None}


def pascal_to_snake(obj: Any) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", getattr(obj, "__name__", "")).lower()


class Entity(MappedAsDataclass, DeclarativeBase, init=False):
    id: Any

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return pascal_to_snake(cls)

    def as_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        if exclude_none:
            return asdict(self, dict_factory=_filter_none)

        return asdict(self)
