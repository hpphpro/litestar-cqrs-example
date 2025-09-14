from __future__ import annotations

import uuid as _uuid

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app.contracts.manager import TransactionManager
from tests.integration.conftest import *  # noqa: F403
from tests.integration.utils import create_superuser_and_token


async def test_user_detail_404_with_admin(
    client: AsyncTestClient[Litestar], manager: TransactionManager
) -> None:
    token, _ = await create_superuser_and_token(client, manager)

    missing_id = _uuid.uuid4()
    resp = await client.get(
        f"/v1/private/users/{missing_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
