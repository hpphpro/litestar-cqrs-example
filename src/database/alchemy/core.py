from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.database.interfaces.connection import AsyncConnection


def create_sa_engine(url: str, **options: Any) -> AsyncEngine:
    return create_async_engine(url, **options)


class ConnectionFactory:
    __slots__ = ("_engine",)

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def __call__(self) -> AsyncConnection:
        return self.create_connection()

    @classmethod
    def from_url(cls, url: str, **options: Any) -> ConnectionFactory:
        return cls(create_sa_engine(url=url, **options))

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def create_connection(self) -> AsyncConnection:
        return async_sessionmaker(self.engine, expire_on_commit=False, autoflush=False)()
