from functools import partial
from typing import Any, cast

from src.api.common.interfaces.middleware import CallNextHandlerMiddlewareType, MiddlewareType


def wrap_middleware(
    call_next: CallNextHandlerMiddlewareType, *middlewares: MiddlewareType, **kw: Any
) -> CallNextHandlerMiddlewareType:
    middleware = partial(call_next, **kw)

    for m in reversed(middlewares):
        middleware = partial(m, middleware)

    return cast(CallNextHandlerMiddlewareType, middleware)
