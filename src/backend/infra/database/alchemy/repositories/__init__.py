from collections.abc import Callable
from typing import Any

from backend.app.contracts.manager import TransactionManager
from backend.app.contracts.repositories import RbacRepository, UserRepository

from .rbac import RbacRepositoryImpl
from .user import UserRepositoryImpl


class RepositoryGatewayImpl:
    __slots__ = ("_manager", "_service_cache")

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager
        self._service_cache: dict[str, Any] = {}

    @property
    def manager(self) -> TransactionManager:
        return self._manager

    @property
    def user(self) -> UserRepository:
        return self._get_or_create("user", UserRepositoryImpl, self._manager)

    @property
    def rbac(self) -> RbacRepository:
        return self._get_or_create("rbac", RbacRepositoryImpl, self._manager)

    def _get_or_create[**P, S](
        self, key: str, factory: Callable[P, S], *args: P.args, **kw: P.kwargs
    ) -> S:
        if not (service := self._service_cache.get(key)):
            service = factory(*args, **kw)

            self._service_cache[key] = service

        return service
