from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from types import TracebackType
from typing import Any, cast

from src.database.interfaces.connection import AsyncConnection, IsolationLevel
from src.database.interfaces.manager import TransactionManager
from src.database.interfaces.query import Query


class TransactionManagerImpl:
    __slots__ = (
        "conn",
        "_is_tx_opened",
    )

    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn
        self._is_tx_opened = False

    async def send[C: AsyncConnection, T](self, query: Query[C, T], /, **kw: Any) -> T:
        return await query(cast(C, self.conn), **kw)

    __call__ = send

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._is_tx_opened:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()

        await self.close_transaction()

    async def __aenter__(self) -> TransactionManagerImpl:
        await self.conn.__aenter__()
        return self

    async def commit(self) -> None:
        await self.conn.commit()

    async def rollback(self) -> None:
        await self.conn.rollback()

    async def with_transaction(
        self, isolation_level: IsolationLevel | None = None, nested: bool = False
    ) -> TransactionManagerImpl:
        assert self.conn.is_active, "Cannot start transaction on closed connection"

        try:
            if not self.conn.in_transaction() and not nested:
                await self.conn.begin()
            elif nested and self.conn.in_transaction():
                await self.conn.begin_nested()
            else:
                raise AssertionError("You cannot start nested transaction with isolation level")
            self._is_tx_opened = True
        finally:
            if isolation_level:
                driver = await self.conn.connection()
                await driver.exec_driver_sql(
                    f"SET TRANSACTION ISOLATION LEVEL {isolation_level.upper()}"
                )

        return self

    async def close_transaction(self) -> None:
        await self.conn.__aexit__(None, None, None)


class ManagerFactory:
    __slots__ = (
        "_as_context_manager",
        "_conn_factory",
    )

    def __init__(
        self, conn_factory: Callable[[], AsyncConnection], as_context_manager: bool = False
    ) -> None:
        self._conn_factory = conn_factory
        self._as_context_manager = as_context_manager

    def __call__(
        self,
    ) -> TransactionManagerImpl | AbstractAsyncContextManager[TransactionManager]:
        if self._as_context_manager:
            return self.make_manager_context()

        return self.make_transaction_manager()

    def make_transaction_manager(self) -> TransactionManager:
        return TransactionManagerImpl(conn=self._conn_factory())

    @asynccontextmanager
    async def make_manager_context(self) -> AsyncIterator[TransactionManager]:
        async with TransactionManagerImpl(conn=self._conn_factory()) as manager:
            yield manager
