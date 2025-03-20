import uuid
from typing import Protocol, Unpack, runtime_checkable

from src.common import exceptions as exc
from src.database.alchemy import entity, queries
from src.database.alchemy.types import OffsetPaginationResult, OrderBy
from src.database.interfaces.manager import TransactionManager
from src.services import tools
from src.services.internal.user.types import UserCreate, UserUpdate


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
    async def exists(self, id: uuid.UUID) -> None: ...


class UserServiceImpl:
    __slots__ = ("_manager",)

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager

    async def get_one(self, id: uuid.UUID) -> entity.User:
        result = await self._manager.send(queries.base.GetOne.with_(entity.User)(id=id))

        if not result:
            raise exc.NotFoundError("No such user")

        return result

    async def get_many_by_offset(
        self,
        offset: int,
        limit: int,
        order_by: OrderBy = "ASC",
    ) -> OffsetPaginationResult[entity.User]:
        result = await self._manager.send(
            queries.base.GetManyByOffset.with_(entity.User)(
                offset=offset, limit=limit, order_by=order_by
            )
        )

        return result

    @tools.on_error("login", should_raise=exc.ConflictError)
    async def create(self, **data: Unpack[UserCreate]) -> entity.User:
        result = await self._manager.send(queries.base.Create.with_(entity.User)(**data))

        if not result:
            raise exc.ConflictError("User already exists")

        return result

    @tools.on_error("login", should_raise=exc.ConflictError)
    async def update(self, id: uuid.UUID, **data: Unpack[UserUpdate]) -> entity.User:
        await self.exists(id)
        result = await self._manager.send(
            queries.base.Update.with_(entity.User)(data).filter(id=id)
        )

        if not result:
            raise exc.ConflictError("User were not updated", id=id)

        return result[0]

    @tools.on_error(
        base_message="User cannot be deleted: {reason}", should_raise=exc.BadRequestError
    )
    async def delete(self, id: uuid.UUID) -> bool:
        await self.exists(id)
        result = await self._manager.send(queries.base.Delete.with_(entity.User)(id=id))

        return bool(result)

    async def exists(self, id: uuid.UUID) -> None:
        result = await self._manager.send(queries.base.Exists.with_(entity.User)(id=id))

        if not result:
            raise exc.NotFoundError("No such user")
