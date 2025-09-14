from __future__ import annotations

from collections.abc import Generator
from typing import Any, Protocol, runtime_checkable

from backend.app.contracts.dto import DTO

from .event import Event
from .handler import Handler, HandlerType


class AwaitableProxy[_: HandlerType]:
    __slots__ = (
        "_context",
        "_handler",
        "_qte",
    )

    def __init__[T, Q: DTO, R](self, handler: Handler[T, Q, R], context: T, qce: Q) -> None:
        self._handler = handler
        self._context = context
        self._qte = qce

    def __await__[T, Q: DTO, R](
        self: AwaitableProxy[Handler[T, Q, R]],
    ) -> Generator[Any, None, R]:
        return (
            yield from self._handler(self._context, self._qte).__await__()  # type: ignore[return-value]
        )


@runtime_checkable
class QCBusType(Protocol):
    def __call__[T, Q: DTO, R](self, context: T, qc: Q, /) -> AwaitableProxy[Handler[T, Q, R]]: ...
    def send_unwrapped[T, Q: DTO, R](
        self,
        context: T,
        qc: Q,
        /,
    ) -> AwaitableProxy[Handler[T, Q, R]]: ...


@runtime_checkable
class EventBusType(Protocol):
    async def publish[E: Event](self, event: E, /, **kw: Any) -> None: ...
