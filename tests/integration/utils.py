import uuid
from typing import Any, cast

import sqlalchemy as sa
from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.auth import Action, Effect, Source
from backend.app.contracts.connection import AsyncConnection
from backend.app.contracts.manager import TransactionManager
from backend.app.contracts.query import Query
from backend.app.contracts.types.user import CreateUserData
from backend.infra.database.alchemy import entity, queries
from tests.integration.conftest import *  # noqa: F403


async def _exec[C: AsyncConnection, T](manager: TransactionManager, query: Query[C, T]) -> T:
    return await manager.send(query)


async def refresh_permissions_mv(manager: TransactionManager) -> None:
    await manager.conn.execute(sa.text("REFRESH MATERIALIZED VIEW mv_user_permissions;"))


async def create_role(
    manager: TransactionManager, name: str, level: int, *, is_superuser: bool = False
) -> uuid.UUID:
    role = await _exec(
        manager,
        queries.base.CreateOrIgnore[entity.Role](name=name, level=level, is_superuser=is_superuser),
    )

    assert role is not None, "Role creation failed"

    return role.id



async def create_field(
    manager: TransactionManager, permission_id: uuid.UUID, src: Source, name: str
) -> uuid.UUID:
    field = await _exec(
        manager,
        queries.base.CreateOrIgnore[entity.PermissionField](
            permission_id=permission_id, src=src, name=name
        ),
    )
    assert field is not None, "Field creation failed"

    return field.id


async def grant_role_permission(
    manager: TransactionManager,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    scope: str,
) -> None:
    await _exec(
        manager,
        queries.base.CreateOrIgnore[entity.RolePermission](
            role_id=role_id, permission_id=permission_id, scope=scope
        ),
    )


async def grant_role_field(
    manager: TransactionManager,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    field_id: uuid.UUID,
    effect: Effect,
) -> None:
    await _exec(
        manager,
        queries.base.CreateOrIgnore[entity.RolePermissionField](
            role_id=role_id, permission_id=permission_id, field_id=field_id, effect=effect
        ),
    )


async def assign_role(manager: TransactionManager, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
    await _exec(
        manager,
        queries.base.CreateOrIgnore[entity.UserRole](user_id=user_id, role_id=role_id),
    )


async def create_user(
    client: AsyncTestClient[Litestar], email: str, password: str
) -> uuid.UUID:
    data = CreateUserData(email=email, password=password)
    resp = await client.post(f"/v1/public/users", json=data.as_dict())

    assert resp.status_code == 201, resp.text

    return uuid.UUID(resp.json()["id"])


async def login_and_get_token(
    client: AsyncTestClient[Litestar], email: str, password: str
) -> str:
    payload = {"fingerprint": "test_fp", "email": email, "password": password}
    resp = await client.post(f"/v1/public/auth/login", json=payload)
    data = resp.json()

    assert resp.status_code == 200 and data.get("token") is not None

    token: str = data.get("token", "")

    return token


async def create_superuser_and_token(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> tuple[str, str]:
    email = "admin_rbac@test.com"
    password = "password_1"

    admin_id = await create_user(client, email, password)
    owner_role_id = await create_role(manager, "owner", 1000, is_superuser=True)
    await assign_role(manager, admin_id, owner_role_id)
    await refresh_permissions_mv(manager)
    await manager.commit()

    token = await login_and_get_token(client, email, password)
    return token, email


async def list_permissions(
    client: AsyncTestClient[Litestar], admin_token: str
) -> list[dict[str, Any]]:
    resp = await client.get(
        f"/v1/private/rbac/permissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert isinstance(data, list)

    return cast(list[dict[str, Any]], data)


async def find_permission_id(
    client: AsyncTestClient[Litestar],
    admin_token: str,
    *,
    resource: str,
    action: str,
    operation: str,
) -> uuid.UUID:
    perms = await list_permissions(client, admin_token)
    for p in perms:
        if (
            p.get("resource") == resource
            and str(p.get("action")) == action
            and p.get("operation") == operation
        ):
            return uuid.UUID(str(p["id"]))

    raise AssertionError(f"Permission not found: {resource}:{action}:{operation}")


async def find_permission_field_id(
    client: AsyncTestClient[Litestar],
    admin_token: str,
    *,
    resource: str,
    action: str,
    operation: str,
    field_name: str,
    src: str,
) -> uuid.UUID:
    perms = await list_permissions(client, admin_token)
    for p in perms:
        if (
            p.get("resource") == resource
            and str(p.get("action")) == action
            and p.get("operation") == operation
        ):
            fields = cast(list[dict[str, Any]], p.get("fields") or [])
            for f in fields:
                if str(f.get("src")) == src and f.get("name") == field_name:
                    return uuid.UUID(str(f["id"]))

    raise AssertionError(
        f"Permission field not found: {resource}:{action}:{operation} -> {src}:{field_name}"
    )
