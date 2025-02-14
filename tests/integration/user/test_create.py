from tests.integration.conftest import *  # noqa

from litestar import Litestar
from litestar.testing import AsyncTestClient
from src.api.v1.commands.user.create import CreateUser


async def test_user_create_success(client: AsyncTestClient[Litestar]) -> None:
    user = CreateUser(login="test", password="test_test")

    response = await client.post("/api/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None


async def test_user_create_same_login_failed(client: AsyncTestClient[Litestar]) -> None:
    user = CreateUser(login="test", password="test_test2")

    response = await client.post("/api/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None

    user2 = CreateUser(login="test", password="test_test3")

    response = await client.post("/api/v1/users", json=user2.as_mapping())

    assert response.status_code == 409
