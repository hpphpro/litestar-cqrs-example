import abc
from typing import Any

from src.api.common.interfaces.dto import DTO


class Handler[T, Q: DTO, R](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__(self, request: T, qc: Q, /, **kw: Any) -> R: ...


type HandlerType = Handler[Any, Any, Any]
