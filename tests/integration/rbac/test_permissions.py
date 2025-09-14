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
    login_and_get_token,
    refresh_permissions_mv,
    create_superuser_and_token,
)


async def test_set_and_unset_role_affects_permissions(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    viewer = await create_role(manager, "viewer", 10)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    await manager.commit()

    r = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(viewer),
            "permission_id": str(perm),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201

    # create user and assign role
    user_id = await create_user(client, "alice@test.com", "password_1")
    r2 = await client.post(
        f"/v1/private/rbac/roles/{viewer}/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201

    # refresh mv to apply changes
    await refresh_permissions_mv(manager)
    await manager.commit()

    # alice can list users now
    user_token = await login_and_get_token(client, "alice@test.com", "password_1")
    ok = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert ok.status_code == 200

    # unset role
    r3 = await client.delete(
        f"/v1/private/rbac/roles/{viewer}/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 204

    # refresh mv again
    await refresh_permissions_mv(manager)
    await manager.commit()

    # alice cannot list users anymore
    denied = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert denied.status_code == 403


async def test_update_role_level_changes_precedence(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    # two roles with different levels
    low = await create_role(manager, "low_view", 10)
    high = await create_role(manager, "high_view", 20)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    await manager.commit()

    # grant permission ONLY to the higher role first
    g_high = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(high),
            "permission_id": str(perm),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g_high.status_code == 201

    # create user with both roles
    uid = await create_user(client, "carol@test.com", "password_1")
    for role_id in (low, high):
        r2 = await client.post(
            f"/v1/private/rbac/roles/{role_id}/users/{uid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 201

    await refresh_permissions_mv(manager)
    await manager.commit()

    t = await login_and_get_token(client, "carol@test.com", "password_1")

    # allowed because higher role has the permission
    allowed_initial = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert allowed_initial.status_code == 200

    # now lower the 'high' role level below 'low' so that higher role lacks permission
    r3 = await client.patch(
        f"/v1/private/rbac/roles/{high}",
        json={"level": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200

    await refresh_permissions_mv(manager)
    await manager.commit()

    # still allowed due to fallback to the (now lower) role which has the permission
    allowed_fallback = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert allowed_fallback.status_code == 200

    # revoke permission from the role so that no roles grant it -> should be forbidden
    d = await client.delete(
        f"/v1/private/rbac/roles/{high}/permissions/{perm}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert d.status_code == 204

    await refresh_permissions_mv(manager)
    await manager.commit()

    denied_final = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert denied_final.status_code == 403


async def test_fallback_to_lower_role_when_higher_has_no_permission(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    low = await create_role(manager, "low_view", 10)
    high = await create_role(manager, "high_no_perm", 20)
    perm = await find_permission_id(
        client, token, resource="users", action=Action.READ, operation="list"
    )
    await manager.commit()

    # grant only to low role
    g = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(low),
            "permission_id": str(perm),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g.status_code == 201

    uid = await create_user(client, "fb1@test.com", "password_1")
    for role_id in (low, high):
        r2 = await client.post(
            f"/v1/private/rbac/roles/{role_id}/users/{uid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 201

    await refresh_permissions_mv(manager)
    await manager.commit()

    t = await login_and_get_token(client, "fb1@test.com", "password_1")
    ok = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert ok.status_code == 200

    # revoke permission from low so that no roles grant it -> should deny
    g2 = await client.delete(
        f"/v1/private/rbac/roles/{low}/permissions/{perm}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g2.status_code == 204
    await refresh_permissions_mv(manager)
    await manager.commit()

    denied = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert denied.status_code == 403



async def test_grant_permission_invalid_permission_id_conflict(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "grant_invalid", 1)
    await manager.commit()

    import uuid as _uuid

    bad = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role_id),
            "permission_id": str(_uuid.uuid4()),
            "scope": Scope.ANY.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad.status_code == 409
