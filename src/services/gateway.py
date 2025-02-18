from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable

from src.database.interfaces.manager import TransactionManager
from src.services.internal.user.core import UserService, UserServiceImpl


@runtime_checkable
class ServiceGateway(Protocol):
    @property
    def manager(self) -> TransactionManager: ...
    @property
    def user(self) -> UserService: ...


class _ServiceCache(TypedDict, total=False):
    user: UserService


class ServiceGatewayImpl:
    __slots__ = (
        "_manager",
        "_cache",
    )

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager
        self._cache: _ServiceCache = {}

    @property
    def manager(self) -> TransactionManager:
        return self._manager

    @property
    def user(self) -> UserService:
        return self._cache.setdefault("user", UserServiceImpl(self._manager))
