from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from tests.integration.conftest import *  # noqa: F403


async def test_create_user_success(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub1@test.com", "password": "password_1"}
    r = await client.post(f"/v1/public/users", json=payload)

    assert r.status_code == 201
    assert r.json()["id"]



async def test_create_user_invalid_email(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "not-an-email", "password": "password_1"}
    r = await client.post(f"/v1/public/users", json=payload)
    assert r.status_code == 400
