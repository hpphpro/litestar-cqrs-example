from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypedDict, cast, runtime_checkable

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
        return self._get_or_create("user", UserServiceImpl)

    def _get_or_create[S](self, key: str, factory: Callable[..., S]) -> S:
        if not (service := self._cache.get(key)):
            service = factory(self._manager)

            self._cache[key] = service  # type: ignore[literal-required]

        return cast(S, service)
