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


async def test_get_user_detail_success_and_forbidden(
    manager: TransactionManager, client: AsyncTestClient[Litestar]
) -> None:
    admin_token, _ = await create_superuser_and_token(client, manager)
    viewer = await create_role(manager, "viewer_u", 5)
    await manager.commit()
    perm_id = await find_permission_id(
        client, admin_token, resource="users", action=Action.READ, operation="detail"
    )
    r = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(viewer),
            "permission_id": str(perm_id),
            "scope": Scope.OWN.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201

    u1 = await create_user(client, "pv1@test.com", "password_1")
    u2 = await create_user(client, "pv2@test.com", "password_1")
    await assign_role(manager, u1, viewer)
    await refresh_permissions_mv(manager)
    await manager.commit()

    t1 = await login_and_get_token(client, "pv1@test.com", "password_1")

    ok = await client.get(
        f"/v1/private/users/{u1}",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert ok.status_code == 200

    denied = await client.get(
        f"/v1/private/users/{u2}",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert denied.status_code == 403


async def test_get_me_requires_auth(client: AsyncTestClient[Litestar]) -> None:
    resp = await client.get(f"/v1/private/users/me")

    assert resp.status_code == 401


async def test_list_users_without_permission_forbidden(
    client: AsyncTestClient[Litestar]
) -> None:
    # create simple user
    await client.post(
        f"/v1/public/users",
        json={"email": "np1@test.com", "password": "password_1"},
    )
    t = (
        await client.post(
            f"/v1/public/auth/login",
            json={"fingerprint": "fp", "email": "np1@test.com", "password": "password_1"},
        )
    ).json()["token"]

    denied = await client.get(
        f"/v1/private/users",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert denied.status_code == 403
