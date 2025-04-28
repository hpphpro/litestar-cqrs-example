from __future__ import annotations

from src.database.interfaces.manager import TransactionManager
from src.services.internal.interfaces import UserService
from src.services.internal.user import UserServiceImpl
from src.services.mixins import CacheableServiceMixin


class InternalGatewayImpl(CacheableServiceMixin):
    __slots__ = ("_manager",)

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager
        super().__init__()

    @property
    def manager(self) -> TransactionManager:
        return self._manager

    @property
    def user(self) -> UserService:
        return self._get_or_create("user", UserServiceImpl, self._manager)
