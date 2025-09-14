from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from tests.integration.conftest import *  # noqa: F403


async def test_login_success(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub2@test.com", "password": "password_1"}
    r1 = await client.post(f"/v1/public/users", json=payload)
    assert r1.status_code == 201

    login = await client.post(
        f"/v1/public/auth/login",
        json={"fingerprint": "fp", **payload},
    )
    assert login.status_code == 200
    assert login.json().get("token")


async def test_login_invalid_password_unauthorized(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub3@test.com", "password": "password_1"}
    r1 = await client.post(f"/v1/public/users", json=payload)
    assert r1.status_code == 201

    bad = await client.post(
        f"/v1/public/auth/login",
        json={"fingerprint": "fp", "email": payload["email"], "password": "wrong"},
    )

    assert bad.status_code == 401
