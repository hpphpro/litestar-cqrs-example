import abc
from dataclasses import dataclass, is_dataclass
from typing import Any, dataclass_transform

from src.api.common.interfaces.dto import DTO


@dataclass_transform()
class Handler[T, Q: DTO, R](abc.ABC):
    __slots__ = ()

    def __init_subclass__(cls, **kw: Any) -> None:
        if not is_dataclass(cls):
            dataclass(slots=kw.pop("slots", True), **kw)(cls)

    @abc.abstractmethod
    async def __call__(self, request: T, qc: Q, /, **kw: Any) -> R: ...


type HandlerType = Handler[Any, Any, Any]
