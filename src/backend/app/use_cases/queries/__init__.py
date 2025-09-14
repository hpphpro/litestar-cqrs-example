from typing import Any, Protocol, overload, runtime_checkable

from backend.app.bus.interfaces.bus import AwaitableProxy
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts.auth import Context
from backend.app.contracts.dto import DTO

from . import rbac, user


__all__ = ("rbac", "user")


@runtime_checkable
class QueryBus(Protocol):
    # rbac
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.get.GetAllPermissionsQuery,
        /,
    ) -> AwaitableProxy[rbac.get.GetPermissionsQueryHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.get.GetUserPermissionsQuery,
        /,
    ) -> AwaitableProxy[rbac.get.GetUserPermissionsQueryHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.get.GetUserRolesQuery,
        /,
    ) -> AwaitableProxy[rbac.get.GetUserRolesQueryHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.get.GetRoleUsersQuery,
        /,
    ) -> AwaitableProxy[rbac.get.GetRoleUsersQueryHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.get.GetAllRolesQuery,
        /,
    ) -> AwaitableProxy[rbac.get.GetAllRolesQueryHandler]: ...
    # user
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: user.get.GetOneUserQuery,
        /,
    ) -> AwaitableProxy[user.get.GetOneUserQueryHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: user.get.GetManyOffsetUserQuery,
        /,
    ) -> AwaitableProxy[user.get.GetManyOffsetUserQueryHandler]: ...
    def send_unwrapped[R, Q: DTO, T](
        self,
        context: R,
        qc: Q,
        /,
        **kw: Any,
    ) -> AwaitableProxy[Handler[R, Q, T]]: ...

    __call__ = send_unwrapped  # type: ignore[misc]
