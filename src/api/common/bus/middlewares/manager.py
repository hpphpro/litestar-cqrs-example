from collections.abc import Sequence
from functools import partial
from typing import Any, cast, overload

from src.api.common.interfaces.middleware import CallNextHandlerMiddlewareType, MiddlewareType


class HandlerMiddlewareManager(Sequence[MiddlewareType]):
    def __init__(self, *middlewares: MiddlewareType) -> None:
        self._middlewares: list[MiddlewareType] = list(middlewares)

    def register(self, middleware: MiddlewareType) -> MiddlewareType:
        self._middlewares.append(middleware)
        return middleware

    __call__ = register

    def unregister(self, middleware: MiddlewareType) -> None:
        self._middlewares.remove(middleware)

    @overload
    def __getitem__(self, item: int) -> MiddlewareType: ...
    @overload
    def __getitem__(self, item: slice) -> Sequence[MiddlewareType]: ...
    def __getitem__(self, item: int | slice) -> MiddlewareType | Sequence[MiddlewareType]:
        return self._middlewares[item]

    def __len__(self) -> int:
        return len(self._middlewares)

    def wrap_middleware(
        self, call_next: CallNextHandlerMiddlewareType, **kw: Any
    ) -> CallNextHandlerMiddlewareType:
        middleware = partial(call_next, **kw)

        for m in reversed(self._middlewares):
            middleware = partial(m, middleware)

        return cast(CallNextHandlerMiddlewareType, middleware)
