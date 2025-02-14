from dataclasses import dataclass, field
from typing import Any, cast, override

from litestar import Request
from litestar.config.response_cache import default_cache_key_builder
from litestar.datastructures import State

from src.api.common.interfaces.dto import DTO
from src.api.common.interfaces.middleware import CallNextHandlerMiddlewareType, HandlerMiddleware
from src.services.interfaces.cache import StrCache


@dataclass(frozen=True, slots=True)
class CacheMiddleware(HandlerMiddleware[Request[None, None, State] | None]):
    cache: StrCache
    cache_time: float = field(default=10)

    @override
    async def __call__[Q: DTO, R: DTO | None](
        self,
        call_next: CallNextHandlerMiddlewareType,
        request: Request[None, None, State] | None,
        qce: Q,
        /,
        **kw: Any,
    ) -> R:
        if not request:
            return await call_next(request, qce, **kw)

        key = f"{request.base_url}/{default_cache_key_builder(request)}"
        value = await self.cache.get(key)
        if value:
            return cast(R, value)

        result: R = await call_next(request, qce, **kw)
        if isinstance(result, DTO):
            await self.cache.set(key, result.as_string(), expire=self.cache_time)

        return result


@dataclass(frozen=True, slots=True)
class CacheInvalidateMiddleware(HandlerMiddleware[Request[None, None, State] | None]):
    cache: StrCache

    @override
    async def __call__[Q: DTO, R: DTO | None](
        self,
        call_next: CallNextHandlerMiddlewareType,
        request: Request[None, None, State] | None,
        qce: Q,
        /,
        **kw: Any,
    ) -> R:
        if not request:
            return await call_next(request, qce, **kw)

        await self.cache.delete(f"{request.base_url}*")

        return await call_next(request, qce, **kw)
