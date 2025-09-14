from typing import Any, Protocol, overload, runtime_checkable

from backend.app.bus.interfaces.bus import AwaitableProxy
from backend.app.bus.interfaces.handler import Handler
from backend.app.contracts.auth import Context
from backend.app.contracts.dto import DTO

from . import auth, rbac, user


__all__ = (
    "auth",
    "user",
)


@runtime_checkable
class CommandBus(Protocol):
    # rbac
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.create.CreateRoleCommand,
        /,
    ) -> AwaitableProxy[rbac.create.CreateRoleCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.update.UpdateRoleCommand,
        /,
    ) -> AwaitableProxy[rbac.update.UpdateRoleCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.create.GrantRolePermissionCommand,
        /,
    ) -> AwaitableProxy[rbac.create.GrantRolePermissionCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.create.SetRoleCommand,
        /,
    ) -> AwaitableProxy[rbac.create.SetRoleCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.create.GrantPermissionCommand,
        /,
    ) -> AwaitableProxy[rbac.create.GrantPermissionCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.create.GrantPermissionFieldCommand,
        /,
    ) -> AwaitableProxy[rbac.create.GrantPermissionFieldCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.delete.RevokePermissionCommand,
        /,
    ) -> AwaitableProxy[rbac.delete.RevokePermissionCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.delete.RevokePermissionFieldCommand,
        /,
    ) -> AwaitableProxy[rbac.delete.RevokePermissionFieldCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.delete.UnsetRoleCommand,
        /,
    ) -> AwaitableProxy[rbac.delete.UnsetRoleCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: rbac.update.UpdatePermissionFieldCommand,
        /,
    ) -> AwaitableProxy[rbac.update.UpdatePermissionFieldCommandHandler]: ...

    # auth
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: auth.login.LoginUserCommand,
        /,
    ) -> AwaitableProxy[auth.login.LoginUserCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: auth.logout.LogoutUserCommand,
        /,
    ) -> AwaitableProxy[auth.logout.LogoutUserCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: auth.refresh.RefreshUserCommand,
        /,
    ) -> AwaitableProxy[auth.refresh.RefreshUserCommandHandler]: ...
    # user
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: user.create.CreateUserCommand,
        /,
    ) -> AwaitableProxy[user.create.CreateUserCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: user.delete.DeleteUserCommand,
        /,
    ) -> AwaitableProxy[user.delete.DeleteUserCommandHandler]: ...
    @overload
    def send_unwrapped(
        self,
        context: Context,
        qc: user.update.UpdateUserCommand,
        /,
    ) -> AwaitableProxy[user.update.UpdateUserCommandHandler]: ...

    def send_unwrapped[R, Q: DTO, T](
        self,
        context: R,
        qc: Q,
        /,
        **kw: Any,
    ) -> AwaitableProxy[Handler[R, Q, T]]: ...

    __call__ = send_unwrapped  # type: ignore[misc]
