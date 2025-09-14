from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final, override

from backend.app.bus.interfaces.middleware import (
    CallNextHandlerMiddlewareType,
    HandlerMiddleware,
)
from backend.app.common.tools import msgspec_encoder
from backend.app.contracts.auth import Context
from backend.app.contracts.cache import StrCache
from backend.app.contracts.dto import DTO


EPOCH_KEY: Final[str] = "cache:epoch"


@dataclass(frozen=True, slots=True)
class CacheMiddleware(HandlerMiddleware[Context]):
    cache: StrCache
    cache_key_builder: Callable[[Context], str]
    cache_time: float = field(default=60)

    async def _epoch(self) -> int:
        return (int(v) if (v := await self.cache.get(EPOCH_KEY)) else 0) % 1_000_000

    @override
    async def __call__[Q: DTO, R](
        self,
        call_next: CallNextHandlerMiddlewareType,
        context: Context,
        qce: Q,
        /,
    ) -> R:
        key = f"{await self._epoch()}:{self.cache_key_builder(context)}"
        if value := await self.cache.get(key):
            return value  # type: ignore[return-value]

        result: R = await call_next(context, qce)

        if result:
            await self.cache.set(key, msgspec_encoder(result), expire=self.cache_time)

        return result


@dataclass(frozen=True, slots=True)
class CacheInvalidateMiddleware(HandlerMiddleware[Context]):
    cache: StrCache

    @override
    async def __call__[Q: DTO, R](
        self,
        call_next: CallNextHandlerMiddlewareType,
        context: Context,
        qce: Q,
        /,
    ) -> R:
        result: R = await call_next(context, qce)

        await self.cache.increment(EPOCH_KEY)

        return result
