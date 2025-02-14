from typing import Any, Protocol, overload, runtime_checkable

from litestar import Request
from litestar.datastructures import State

from src.api.common.interfaces.handler import Handler
from src.api.common.interfaces.proxy import AwaitableProxy
from src.api.v1.queries import user as user


@runtime_checkable
class QueryBus(Protocol):
    # user
    @overload
    def send_unwrapped(
        self,
        request: Request[None, None, State],
        qc: user.get.GetOneUser,
        /,
    ) -> AwaitableProxy[user.get.GetOneUserHandler]: ...
    @overload
    def send_unwrapped(
        self,
        request: Request[None, None, State],
        qc: user.get.GetManyOffsetUser,
        /,
    ) -> AwaitableProxy[user.get.GetManyOffsetUserHandler]: ...

    def send_unwrapped(
        self, request: Any, qc: Any, /, **kw: Any
    ) -> AwaitableProxy[Handler[Any, Any, Any]]: ...

    __call__ = send_unwrapped  # type: ignore[misc]
