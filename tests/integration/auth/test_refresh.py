from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from tests.integration.conftest import *  # noqa: F403


async def test_refresh_success(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub4@test.com", "password": "password_1"}
    r1 = await client.post(f"/v1/public/users", json=payload)
    assert r1.status_code == 201

    login = await client.post(
        f"/v1/public/auth/login",
        json={"fingerprint": "fp", **payload},
    )
    assert login.status_code == 200

    refresh = await client.post(
        f"/v1/public/auth/refresh",
        json={"fingerprint": "fp"},
        cookies={"refresh": login.cookies.get("refresh") or ""},
    )
    assert refresh.status_code == 200
    assert refresh.json().get("token")


async def test_refresh_success_with_header(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub4@test.com", "password": "password_1"}
    r1 = await client.post(f"/v1/public/users", json=payload)
    assert r1.status_code == 201

    login = await client.post(
        f"/v1/public/auth/login",
        json={"fingerprint": "fp", **payload},
    )
    assert login.status_code == 200

    refresh = await client.post(
        f"/v1/public/auth/refresh",
        json={"fingerprint": "fp"},
        headers={"Authorization": f"Bearer {login.cookies.get('refresh') or ''}"},
    )
    assert refresh.status_code == 200

    assert refresh.json().get("token")


async def test_refresh_failed_with_invalid_token_header(
    client: AsyncTestClient[Litestar]
) -> None:
    payload = {"email": "pub4@test.com", "password": "password_1"}
    r1 = await client.post(f"/v1/public/users", json=payload)
    assert r1.status_code == 201

    login = await client.post(
        f"/v1/public/auth/login",
        json={"fingerprint": "fp", **payload},
    )
    assert login.status_code == 200

    refresh = await client.post(
        f"/v1/public/auth/refresh",
        json={"fingerprint": "fp"},
        headers={"Authorization": f"NotBearer {login.cookies.get('refresh') or ''}"},
    )
    assert refresh.status_code == 401



async def test_refresh_unauthorized(
    client: AsyncTestClient[Litestar]
) -> None:
    refresh = await client.post(
        f"/v1/public/auth/refresh",
        json={"fingerprint": "fp"},
    )
    assert refresh.status_code == 401
