import uuid
from typing import Any, Protocol, overload, runtime_checkable

from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.dto import DTO
from src.api.common.interfaces.handler import Handler
from src.api.common.interfaces.proxy import AwaitableProxy
from src.api.v1.commands import user as user


@runtime_checkable
class CommandBus(Protocol):
    # user
    @overload
    def send_unwrapped(
        self,
        request: Request[None, None, State],
        qc: user.create.CreateUser,
        /,
    ) -> AwaitableProxy[user.create.CreateUserHandler]: ...
    @overload
    def send_unwrapped(
        self,
        request: Request[None, None, State],
        qc: user.delete.DeleteUser,
        /,
    ) -> AwaitableProxy[user.delete.DeleteUserHandler]: ...
    @overload
    def send_unwrapped(
        self,
        request: Request[None, None, State],
        qc: user.update.UpdateUser,
        /,
        *,
        id: uuid.UUID,
    ) -> AwaitableProxy[user.update.UpdateUserHandler]: ...

    def send_unwrapped[R, Q: DTO, T](
        self, request: R, qc: Q, /, **kw: Any
    ) -> AwaitableProxy[Handler[R, Q, T]]: ...

    __call__ = send_unwrapped  # type: ignore[misc]
