from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Scope
from uuid import UUID
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


async def _grant_update_own(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> tuple[str, UUID]:
    token, _ = await create_superuser_and_token(client, manager)
    role_id = await create_role(manager, "upd_own", level=3)
    await manager.commit()
    perm = await find_permission_id(
        client, token, resource="users", action=Action.UPDATE, operation="update"
    )
    g = await client.post(
        f"/v1/private/rbac/role-permissions",
        json={
            "role_id": str(role_id),
            "permission_id": str(perm),
            "scope": Scope.OWN.value,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert g.status_code == 201
    return token, role_id


async def test_update_self_success_and_other_forbidden(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    _, role_id = await _grant_update_own(client, manager)
    u1 = await create_user(client, "upd1@test.com", "password_1")
    u2 = await create_user(client, "upd2@test.com", "password_1")

    await assign_role(manager, u1, role_id)
    await refresh_permissions_mv(manager)
    await manager.commit()

    t1 = await login_and_get_token(client, "upd1@test.com", "password_1")

    # self OK
    ok = await client.patch(
        f"/v1/private/users/{u1}",
        json={"email": "upd1_new@test.com"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert ok.status_code == 200
    assert ok.json().get("status") is True

    # other forbidden
    denied = await client.patch(
        f"/v1/private/users/{u2}",
        json={"email": "upd2_new@test.com"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert denied.status_code == 403


async def test_update_validation_errors(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    _, role_id = await _grant_update_own(client, manager)
    u1 = await create_user(client, "upd3@test.com", "password_1")
    await assign_role(manager, u1, role_id)
    await refresh_permissions_mv(manager)
    await manager.commit()
    t1 = await login_and_get_token(client, "upd3@test.com", "password_1")

    bad_email = await client.patch(
        f"/v1/private/users/{u1}",
        json={"email": "not-mail"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert bad_email.status_code == 400

    too_short_pwd = await client.patch(
        f"/v1/private/users/{u1}",
        json={"password": "short"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert too_short_pwd.status_code == 400
