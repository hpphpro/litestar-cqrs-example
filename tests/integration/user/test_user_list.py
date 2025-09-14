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


async def test_list_users_own_scope_success_and_mismatch_forbidden(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    admin_token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "viewer_list", level=3)
    await manager.commit()
    perm_id = await find_permission_id(
        client, admin_token, resource="users", action=Action.READ, operation="list"
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

    # create two users and assign role to one of them
    u1 = await create_user(client, "list1@test.com", "password_1")
    u2 = await create_user(client, "list2@test.com", "password_1")
    await assign_role(manager, u1, role_id)
    await refresh_permissions_mv(manager)
    await manager.commit()

    t1 = await login_and_get_token(client, "list1@test.com", "password_1")

    # allowed: filter by own email
    ok = await client.get(
        f"/v1/private/users?email=list1@test.com",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert ok.status_code == 200

    # forbidden: trying to filter by someone else's email with OWN scope
    denied = await client.get(
        f"/v1/private/users?email=list2@test.com",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert denied.status_code == 403
