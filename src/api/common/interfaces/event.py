import abc
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any


def _exclude_filter(exclude: set[str]) -> Callable[[list[tuple[str, Any]]], dict[str, Any]]:
    def inner(values: list[tuple[str, Any]]) -> dict[str, Any]:
        return {k: v for k, v in values if k not in exclude}

    return inner


@dataclass(frozen=True, slots=True)
class Event:
    @property
    def name(self) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", type(self).__name__).lower()

    def __str__(self) -> str:
        return self.name

    def as_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        if exclude:
            return asdict(self, dict_factory=_exclude_filter(exclude))

        return asdict(self)


class EventHandler[E: Event](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__(self, event: E, /, **kw: Any) -> None:
        raise NotImplementedError
