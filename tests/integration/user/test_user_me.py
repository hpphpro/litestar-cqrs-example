from __future__ import annotations

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import create_superuser_and_token


async def test_get_me_success(client: AsyncTestClient[Litestar], manager: TransactionManager) -> None:
    token, email = await create_superuser_and_token(client, manager)

    resp = await client.get(
        f"/v1/private/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("email") == email
