from tests.integration.conftest import *  # noqa

from litestar import Litestar
from litestar.testing import AsyncTestClient
from src.api.v1.commands.user.create import CreateUser


async def test_user_delete_success(client: AsyncTestClient[Litestar]) -> None:
    user = CreateUser(login="test", password="test_test")

    response = await client.post("/api/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None

    deleted = await client.delete(f"/api/v1/users/{data['id']}")

    assert deleted.status_code == 204

    # ensure
    response = await client.get(f"/api/v1/users/{data['id']}")

    assert response.status_code == 404
