import uuid

from backend.app.contracts.auth import AuthUser, Permission, PermissionSpec, Role
from backend.app.contracts.manager import TransactionManager
from backend.infra.database.alchemy import entity, queries
from backend.infra.shared.result import as_result

from .hasher import Argon2


class AuthenticatorImpl:
    __slots__ = ("_hasher",)

    def __init__(self, hasher: Argon2) -> None:
        self._hasher = hasher

    @as_result()
    async def authenticate(
        self,
        manager: TransactionManager,
        *,
        email: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AuthUser | None:
        assert email or user_id, "Either `email` or `user_id` must be provided"

        user = await manager.send(
            queries.base.GetOne[entity.User]("roles", email=email, id=user_id)
        )

        return (
            None
            if not user
            else AuthUser(
                id=user.id,
                email=user.email,
                password=user.password,
                is_superuser=any(role.is_superuser for role in user.roles),
                roles=tuple(Role(name=role.name) for role in user.roles),
            )
        )

    @as_result()
    async def get_permission_for(
        self, user: AuthUser, permission: PermissionSpec, manager: TransactionManager
    ) -> Permission | None:
        return await manager.send(
            queries.user.GetUserPermission(user_id=user.id, permission_key=permission.key())
        )
