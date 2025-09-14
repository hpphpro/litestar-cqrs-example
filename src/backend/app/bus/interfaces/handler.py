import abc
from typing import Any

from backend.app.contracts.dto import DTO


class Handler[T, Q: DTO, R](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__(self, context: T, qc: Q, /) -> R: ...


type HandlerType = Handler[Any, Any, Any]
