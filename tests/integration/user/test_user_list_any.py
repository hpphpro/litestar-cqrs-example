from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Scope
from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import (
    create_role,
    create_superuser_and_token,
    create_user,
    find_permission_id,
    refresh_permissions_mv,
)


async def test_list_users_any_scope_success(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "aud_any", level=4)
    await manager.commit()
    perm_id = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )

    grant = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role_id),
            "permission_id": str(perm_id),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert grant.status_code == 201

    uid = await create_user(client, "any1@test.com", "password_1")
    await refresh_permissions_mv(manager)
    await manager.commit()

    # bearer with any scope may list without email restriction
    r = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    # paginated offset result: { items: [...], ... }
    assert isinstance(data.get("items"), list)
    assert any(u.get("id") == str(uid) for u in data["items"])
