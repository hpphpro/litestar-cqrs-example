from typing import Protocol, runtime_checkable

from .manager import TransactionManager
from .repositories import RbacRepository, UserRepository


@runtime_checkable
class RepositoryGateway(Protocol):
    @property
    def manager(self) -> TransactionManager: ...
    @property
    def user(self) -> UserRepository: ...
    @property
    def rbac(self) -> RbacRepository: ...
