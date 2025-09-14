import abc
from typing import Any, Protocol, runtime_checkable

from backend.app.contracts.dto import DTO


@runtime_checkable
class MiddlewareType(Protocol):
    async def __call__(self, *args: Any, **kw: Any) -> Any: ...


class CallNextHandlerMiddlewareType(Protocol):
    async def __call__[T, Q: DTO, R](self, context: T, qc: Q, /) -> R: ...


class HandlerMiddleware[T](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__[Q: DTO, R](
        self,
        call_next: CallNextHandlerMiddlewareType,
        context: T,
        qc: Q,
        /,
    ) -> R:
        raise NotImplementedError
