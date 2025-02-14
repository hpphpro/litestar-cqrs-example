import abc
from typing import Any, Protocol, runtime_checkable

from src.api.common.interfaces.dto import DTO


@runtime_checkable
class MiddlewareType(Protocol):
    async def __call__(self, *args: Any, **kw: Any) -> Any: ...


class CallNextHandlerMiddlewareType(Protocol):
    async def __call__[T, Q: DTO, R: DTO | None](self, request: T, qc: Q, /, **kw: Any) -> R: ...


class HandlerMiddleware[T](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__[Q: DTO, R: DTO | None](
        self,
        call_next: CallNextHandlerMiddlewareType,
        request: T,
        qc: Q,
        /,
        **kw: Any,
    ) -> R:
        raise NotImplementedError
