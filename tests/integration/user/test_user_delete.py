from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Scope
from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import (
    assign_role,
    create_role,
    create_superuser_and_token,
    create_user,
    find_permission_id,
    login_and_get_token,
    refresh_permissions_mv,
)


async def test_delete_self_success_and_other_forbidden(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    admin_token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "deleter", level=3)
    await manager.commit()
    perm_id = await find_permission_id(
        client, admin_token, resource="users", action=Action.DELETE, operation="delete"
    )
    grant = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role_id),
            "permission_id": str(perm_id),
            "scope": Scope.OWN.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert grant.status_code == 201

    u1 = await create_user(client, "del1@test.com", "password_1")
    u2 = await create_user(client, "del2@test.com", "password_1")
    await assign_role(manager, u1, role_id)
    await refresh_permissions_mv(manager)
    await manager.commit()

    t1 = await login_and_get_token(client, "del1@test.com", "password_1")

    ok = await client.delete(
        f"/v1/private/users/{u1}",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert ok.status_code == 204

    denied = await client.delete(
        f"/v1/private/users/{u2}",
        headers={"Authorization": f"Bearer {t1}"},
    )
    # after deleting self, token is no longer valid -> Unauthorized
    assert denied.status_code == 401
