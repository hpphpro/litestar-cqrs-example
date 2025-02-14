import re
from dataclasses import asdict
from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


def _filter_none(values: list[tuple[str, Any]]) -> dict[str, Any]:
    return {k: v for k, v in values if v is not None}


class Entity(MappedAsDataclass, DeclarativeBase, init=False):
    id: Any

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    def as_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        if exclude_none:
            return asdict(self, dict_factory=_filter_none)

        return asdict(self)
