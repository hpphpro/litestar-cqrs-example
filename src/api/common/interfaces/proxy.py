from __future__ import annotations

from collections.abc import Generator
from typing import Any

from src.api.common.interfaces.dto import DTO
from src.api.common.interfaces.handler import Handler, HandlerType


class AwaitableProxy[_: HandlerType]:
    __slots__ = (
        "_handler",
        "_request",
        "_qte",
        "_kw",
    )

    def __init__[T, Q: DTO, R](
        self, handler: Handler[T, Q, R], request: T, qce: Q, **kw: Any
    ) -> None:
        self._handler = handler
        self._request = request
        self._qte = qce
        self._kw = kw

    def __await__[T, Q: DTO, R](
        self: AwaitableProxy[Handler[T, Q, R]],
    ) -> Generator[Any, Any, R]:
        return (
            yield from self._handler(self._request, self._qte, **self._kw).__await__()  # type: ignore[return-value]
        )
