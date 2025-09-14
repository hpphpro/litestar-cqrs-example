from typing import Self, override

import redis.asyncio as aioredis

from backend.app.contracts.shared_lock import SharedLock


class RedisSharedLock(SharedLock):
    __slots__ = ("_lock",)
    redis: aioredis.Redis  # type: ignore[type-arg]

    def __init__(self, name: str, timeout: float | None = None, *, blocking: bool = True) -> None:
        self._lock = self.redis.lock(
            name, timeout=timeout, blocking=blocking, blocking_timeout=blocking * 2
        )

    @classmethod
    def create(cls, redis: aioredis.Redis) -> type[Self]:  # type: ignore[type-arg]
        return type(cls.__name__, (cls,), {"redis": redis})

    @override
    async def locked(self) -> bool:
        return await self._lock.locked()

    @override
    async def acquire(self) -> None:
        await self._lock.acquire()

    @override
    async def release(self) -> None:
        await self._lock.release()
