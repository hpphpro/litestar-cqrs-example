from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Scope
from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import (
    create_role,
    create_user,
    find_permission_id,
    refresh_permissions_mv,
    create_superuser_and_token,
)


async def test_create_and_list_roles(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    payload = {"name": "manager", "level": 50, "is_superuser": False}
    r = await client.post(
        f"/v1/private/rbac/roles",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    role_id = r.json().get("id")
    assert role_id

    r2 = await client.get(
        f"/v1/private/rbac/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert any(item.get("id") == role_id for item in r2.json())


async def test_create_role_conflict(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    payload = {"name": "duprole", "level": 1, "is_superuser": False}
    ok = await client.post(
        f"/v1/private/rbac/roles",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 201

    conflict = await client.post(
        f"/v1/private/rbac/roles",
        json=payload | {"name": "DUPROLE"},  # same name, case-insensitive unique index
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conflict.status_code == 409


async def test_get_user_roles_permissions_and_role_users(
    client: AsyncTestClient[Litestar],  manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role = await create_role(manager, "auditor", 3)
    await manager.commit()
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    # grant
    g = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role),
            "permission_id": str(perm),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g.status_code == 201

    uid = await create_user(client, "aud1@test.com", "password_1")
    set_role = await client.post(
        f"/v1/private/rbac/roles/{role}/users/{uid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert set_role.status_code == 201

    await refresh_permissions_mv(manager)
    await manager.commit()

    # get user roles
    r1 = await client.get(
        f"/v1/private/rbac/users/{uid}/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert any(r.get("id") == str(role) for r in r1.json())

    # get role users
    r2 = await client.get(
        f"/v1/private/rbac/roles/{role}/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert any(u.get("id") == str(uid) for u in r2.json())

    # get user permissions
    r3 = await client.get(
        f"/v1/private/rbac/users/{uid}/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)
