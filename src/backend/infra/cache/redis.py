from datetime import timedelta
from typing import Self

import redis.asyncio as aioredis

from backend.app.contracts.cache import StrCache


def _ensure_string(value: str | bytes) -> str:
    return value.decode() if isinstance(value, bytes) else value


class RedisCache(StrCache):
    __slots__ = ("_redis",)

    def __init__(self, redis: aioredis.Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    @classmethod
    def from_url(cls, url: str) -> Self:
        return cls(aioredis.Redis.from_url(url, decode_responses=True))

    async def get(
        self,
        key: str,
    ) -> str | None:
        result = await self._redis.get(key)

        return _ensure_string(result) if result else None

    async def set(
        self,
        key: str,
        value: str,
        expire: float | timedelta | None = None,
    ) -> None:
        await self._redis.set(key, value, ex=expire)

    async def delete(self, *keys: str) -> None:
        if any("*" in key for key in keys) and (
            found_keys := [found for key in keys async for found in self._redis.scan_iter(key)]
        ):
            await self._redis.delete(*found_keys)
        else:
            await self._redis.delete(*keys)

    async def set_list(
        self,
        key: str,
        *values: str,
        expire: float | timedelta | None = None,
    ) -> None:
        async with self._redis.pipeline() as pipe:
            pipe.lpush(key, *values)
            if expire:
                pipe.expire(
                    key,
                    expire if isinstance(expire, timedelta) else timedelta(seconds=expire),
                )
            await pipe.execute()

    async def get_list(
        self,
        key: str,
    ) -> list[str]:
        return [_ensure_string(v) for v in await self._redis.lrange(key, 0, -1)]

    async def discard(
        self,
        key: str,
        value: str,
    ) -> None:
        await self._redis.lrem(key, 0, value)

    async def clear(self) -> None:
        await self._redis.flushall(asynchronous=True)

    async def exists(self, pattern: str) -> bool:
        return bool(await self._redis.keys(pattern))

    async def keys(self) -> list[str]:
        return await self._redis.keys("*")

    async def increment(self, key: str, amount: int = 1) -> int:
        return await self._redis.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        return await self._redis.decrby(key, amount)

    async def close(self) -> None:
        await self._redis.aclose(close_connection_pool=True)  # type: ignore[attr-defined]
