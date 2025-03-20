import abc
from typing import Any, Protocol, runtime_checkable

from src.database.interfaces.connection import AsyncConnection


@runtime_checkable
class QueryType(Protocol):
    async def __call__[T: AsyncConnection, R](self, conn: T, /, **kw: Any) -> R: ...


class Query[C: AsyncConnection, T](abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    async def __call__(self, conn: C, /, **kw: Any) -> T:
        raise NotImplementedError
