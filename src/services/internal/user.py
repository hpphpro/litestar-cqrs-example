import uuid
from typing import Unpack

from src.common import exceptions as exc
from src.database.alchemy import entity
from src.database.alchemy.types import OffsetPaginationResult, OrderBy, UserCreate, UserUpdate
from src.services import tools
from src.services.internal.base import InternalService


class UserServiceImpl(InternalService[entity.User]):
    __slots__ = ()

    async def get_one(self, id: uuid.UUID) -> entity.User:
        result = await self._dao.get_one(id=id)

        if not result:
            raise exc.NotFoundError("No such user")

        return result

    async def get_many_by_offset(
        self,
        offset: int,
        limit: int,
        order_by: OrderBy = "ASC",
    ) -> OffsetPaginationResult[entity.User]:
        return await self._dao.get_many(offset=offset, limit=limit, order_by=order_by)

    @tools.on_error("login", should_raise=exc.ConflictError)
    async def create(self, **data: Unpack[UserCreate]) -> entity.User:
        result = await self._dao.create(**data)

        if not result:
            raise exc.ConflictError("User already exists")

        return result

    @tools.on_error("login", should_raise=exc.ConflictError)
    async def update(self, id: uuid.UUID, **data: Unpack[UserUpdate]) -> entity.User:
        await self._dao.exists(id=id)
        result = await self._dao.update(data, id=id)

        if not result:
            raise exc.ConflictError("User were not updated", id=id)

        return result[0]

    @tools.on_error(
        base_message="User cannot be deleted: {reason}", should_raise=exc.BadRequestError
    )
    async def delete(self, id: uuid.UUID) -> bool:
        await self._dao.exists(id=id)
        result = await self._dao.delete(id=id)

        return bool(result)
