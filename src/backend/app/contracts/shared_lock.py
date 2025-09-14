import abc
from types import TracebackType
from typing import Self


class SharedLock(abc.ABC):
    __slots__ = (
        "blocking",
        "name",
        "timeout",
    )

    def __init__(self, name: str, timeout: float | None = None, *, blocking: bool = True) -> None:
        self.name = name
        self.timeout = timeout
        self.blocking = blocking

    @abc.abstractmethod
    async def locked(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def acquire(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def release(self) -> None:
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        await self.acquire()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.release()
