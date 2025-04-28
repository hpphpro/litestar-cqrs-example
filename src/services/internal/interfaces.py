import uuid
from typing import Protocol, Unpack, runtime_checkable

from src.database.alchemy import entity
from src.database.alchemy.types import OffsetPaginationResult, OrderBy, UserCreate, UserUpdate
from src.database.interfaces.manager import TransactionManager


@runtime_checkable
class UserService(Protocol):
    async def create(self, **data: Unpack[UserCreate]) -> entity.User: ...
    async def update(self, id: uuid.UUID, **data: Unpack[UserUpdate]) -> entity.User: ...
    async def delete(self, id: uuid.UUID) -> bool: ...
    async def get_one(self, id: uuid.UUID) -> entity.User: ...
    async def get_many_by_offset(
        self,
        offset: int,
        limit: int,
        order_by: OrderBy = "ASC",
    ) -> OffsetPaginationResult[entity.User]: ...


@runtime_checkable
class InternalGateway(Protocol):
    @property
    def manager(self) -> TransactionManager: ...
    @property
    def user(self) -> UserService: ...
