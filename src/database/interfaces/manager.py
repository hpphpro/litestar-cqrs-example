from __future__ import annotations

from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from src.database.interfaces.connection import AsyncConnection, IsolationLevel
from src.database.interfaces.query import Query


@runtime_checkable
class TransactionManager(Protocol):
    conn: AsyncConnection

    async def send[C: AsyncConnection, T](self, query: Query[C, T], /, **kw: Any) -> T: ...
    async def __call__[C: AsyncConnection, T](self, query: Query[C, T], /, **kw: Any) -> T: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def __aenter__(self) -> TransactionManager: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def with_transaction(
        self, isolation_level: IsolationLevel | None = None, nested: bool = False
    ) -> TransactionManager: ...
    async def close_transaction(self) -> None: ...
