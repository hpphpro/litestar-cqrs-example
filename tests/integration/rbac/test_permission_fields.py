from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Effect, Source, Scope
from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import (
    create_role,
    create_user,
    find_permission_field_id,
    find_permission_id,
    login_and_get_token,
    refresh_permissions_mv,
    create_superuser_and_token,
)


async def test_grant_permission_field_and_block_update(
    client: AsyncTestClient[Litestar],  manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    editor = await create_role(manager, "editor", 20)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.UPDATE, operation="update"
    )
    f_password = await find_permission_field_id(
        client,
        token,
        resource="users",
        action=Action.UPDATE,
        operation="update",
        field_name="password",
        src=Source.JSON,
    )
    await manager.commit()

    r = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(editor),
            "permission_id": str(perm),
            "scope": Scope.OWN.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201

    r2 = await client.post(
        f"/v1/private/rbac/permission-fields",
        json={
            "role_id": str(editor),
            "permission_id": str(perm),
            "field_id": str(f_password),
            "effect": Effect.DENY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201

    uid = await create_user(client, "bob@test.com", "password_1")
    r3 = await client.post(
        f"/v1/private/rbac/roles/{editor}/users/{uid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 201

    await refresh_permissions_mv(manager)
    await manager.commit()

    t = await login_and_get_token(client, "bob@test.com", "password_1")

    ok = await client.patch(
        f"/v1/private/users/{uid}",
        json={"email": "bob2@test.com"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert ok.status_code == 200

    denied = await client.patch(
        f"/v1/private/users/{uid}",
        json={"password": "new_password"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert denied.status_code == 403


async def test_list_deny_field_blocks_query_param(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "analyst_list", 1)
    await manager.commit()
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    field = await find_permission_field_id(
        client,
        token,
        resource="users",
        action=Action.READ,
        operation="list",
        field_name="email",
        src=Source.QUERY,
    )

    g = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role_id),
            "permission_id": str(perm),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g.status_code == 201

    g2 = await client.post(
        f"/v1/private/rbac/permission-fields",
        json={
            "role_id": str(role_id),
            "permission_id": str(perm),
            "field_id": str(field),
            "effect": Effect.DENY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g2.status_code == 201

    uid = await create_user(client, "al1@test.com", "password_1")
    set_role = await client.post(
        f"/v1/private/rbac/roles/{role_id}/users/{uid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert set_role.status_code == 201

    await refresh_permissions_mv(manager)
    await manager.commit()

    t = await login_and_get_token(client, "al1@test.com", "password_1")
    ok = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert ok.status_code == 200

    blocked = await client.get(
        f"/v1/private/users",
        params={"email": "x@y.z"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert blocked.status_code == 403


async def test_revoke_permission_and_field_endpoints(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role = await create_role(manager, "revoker", 6)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    field = await find_permission_field_id(
        client,
        token,
        resource="users",
        action=Action.READ,
        operation="list",
        field_name="email",
        src=Source.QUERY,
    )
    await manager.commit()

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
    g2 = await client.post(
        f"/v1/private/rbac/permission-fields",
        json={
            "role_id": str(role),
            "permission_id": str(perm),
            "field_id": str(field),
            "effect": Effect.DENY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g2.status_code == 201

    d1 = await client.delete(
        f"/v1/private/rbac/roles/{role}/permissions/{perm}/fields/{field}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert d1.status_code == 204

    d2 = await client.delete(
        f"/v1/private/rbac/roles/{role}/permissions/{perm}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert d2.status_code == 204


async def test_update_role_permission_field_endpoint_allows_after_update(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role = await create_role(manager, "updater", 7)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.UPDATE, operation="update"
    )
    field = await find_permission_field_id(
        client,
        token,
        resource="users",
        action=Action.UPDATE,
        operation="update",
        field_name="password",
        src=Source.JSON,
    )
    await manager.commit()

    g = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role),
            "permission_id": str(perm),
            "scope": Scope.OWN.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g.status_code == 201
    g2 = await client.post(
        f"/v1/private/rbac/permission-fields",
        json={
            "role_id": str(role),
            "permission_id": str(perm),
            "field_id": str(field),
            "effect": Effect.DENY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g2.status_code == 201

    p = await client.patch(
        f"/v1/private/rbac/roles/{role}/permissions/{perm}/fields/{field}",
        json={"effect": Effect.ALLOW.value},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert p.status_code == 200
